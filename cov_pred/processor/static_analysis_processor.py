from database import Database
from ordered_set import OrderedSet
from utils.format_util import extract_method_from_traces, string_methods
from sklearn.model_selection import train_test_split
from utils.evaluation import evaluate_methods_level
from manager.trace_manager import TraceManager
import json

class StaticAnalysisProcessor:

    def __init__(self, project: str, registry: str, class_method_info: dict,):
        self.project = project
        self.registry = registry
        self.class_method_info = class_method_info

    def analyze(self, collection: dict, signatures_including_logs: list, trace_manager: TraceManager):
        execution_pattern = {}
        train_signatures, validation_signatures = self.split_data(signatures_including_logs)
        results = {}

        validation_oracles = self.validation_oracles(validation_signatures, trace_manager)

        for train_signature in train_signatures:
            for thread_id, logs_executions in collection[train_signature].items():
                for (prev_log, curr_log), executions in logs_executions.items():
                    methods = extract_method_from_traces(executions, self.class_method_info)
                    previous_position = prev_log.get_file() + ":" + str(prev_log.get_line()) if prev_log != "" else "START"
                    current_position = curr_log.get_file() + ":" + str(curr_log.get_line()) if curr_log != "" else "END"
                    if previous_position + '-' + current_position not in execution_pattern:
                        execution_pattern[previous_position + '-' + current_position] = [methods]
                    else:
                        methods_set = execution_pattern[previous_position + '-' + current_position]
                        if methods_set == methods:
                            continue
                        else:
                            execution_pattern[previous_position + '-' + current_position].append(methods)
    

        for validation_signature in validation_signatures:
            predicted_patterns = {}
            predicted_patterns[validation_signature] = OrderedSet()
            for thread_id, logs_executions in collection[validation_signature].items():
                for (prev_log, curr_log), executions in logs_executions.items():
                    methods = extract_method_from_traces(executions, self.class_method_info)
                    previous_position = prev_log.get_file() + ":" + str(prev_log.get_line()) if prev_log != "" else "START"
                    current_position = curr_log.get_file() + ":" + str(curr_log.get_line()) if curr_log != "" else "END"
                    if previous_position + '-' + current_position not in execution_pattern:
                        continue
                    else:
                        patterns = execution_pattern[previous_position + '-' + current_position][0]
                        predicted_patterns[validation_signature].update(patterns)

            precision, recall = evaluate_methods_level(string_methods(predicted_patterns[validation_signature]), validation_oracles[validation_signature])
            results[validation_signature] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        results["average"] = {
            "precision": sum(result["precision"] for result in results.values()) / len(results),
            "recall": sum(result["recall"] for result in results.values()) / len(results),
            "f1": sum(result["f1"] for result in results.values()) / len(results),
        }
        with open(f"output/{self.project}_{self.registry}/static_analysis_metrics_with_class.json", "w") as f:
            json.dump(results, f, indent=4)
    
    def split_data(self, signatures_including_logs: list):
        train_signatures = []
        validation_signatures = []
        test_class = set()
        for signature in signatures_including_logs:
            class_name = signature.split(';')[-1].split('.')[0]
            test_class.add(class_name)
        train_class, validation_class = train_test_split(list(test_class), test_size=0.2, random_state=42)
        for signature in signatures_including_logs:
            class_name = signature.split(';')[-1].split('.')[0]
            if class_name in train_class:
                train_signatures.append(signature)
            elif class_name in validation_class:
                validation_signatures.append(signature)
        return train_signatures, validation_signatures
    
    def validation_oracles(self, validation_signatures: list, trace_manager: TraceManager):
        oracle = {}
        for signature in validation_signatures:
            oracle[signature] = set()
            for thread_id, traces in trace_manager.get_traces_by_signature(signature).items():
                methods = extract_method_from_traces(traces, self.class_method_info)
                oracle[signature].update(methods)
            oracle[signature] = string_methods(oracle[signature])
        
        return oracle
