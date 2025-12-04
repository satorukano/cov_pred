from database import Database
from ordered_set import OrderedSet
from utils.format_util import extract_method_from_traces, string_methods
from sklearn.model_selection import train_test_split
from utils.evaluation import evaluate_methods_level
from utils.format_util import string_traces, get_train_test_split
from manager.trace_manager import TraceManager
from manager.application_log_manager import ApplicationLogManager
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
    
    def identify_log_containing_methods_line(self, application_log_manager: ApplicationLogManager):
        log_containing_methods_line = {}
        train_signatures, validation_signatures = get_train_test_split(self.project, self.registry, application_log_manager.get_signatures_including_logs())
        for signature in validation_signatures:
            if signature not in log_containing_methods_line:
                log_containing_methods_line[signature] = {}
            for thread_id, logs in application_log_manager.get_logs_by_signature(signature).items():
                for log in logs:
                    file = log.get_file()
                    line = int(log.get_line())
                    if file in self.class_method_info:
                        for method_info in self.class_method_info[file]["methods"]:
                            if method_info['start_line'] <= line <= method_info['end_line']:
                                print(f"Log: {log.get_log_statement()} is in Method: {method_info['class_name']}.{method_info['method_name']}")
                                if file.split('/')[-1] not in log_containing_methods_line[signature]:
                                    log_containing_methods_line[signature][file.split('/')[-1]] = set()
                                if method_info['start_line'] == method_info['end_line']:
                                    log_containing_methods_line[signature][file.split('/')[-1]].add(method_info['start_line'])
                                for l in range(method_info['start_line']+1, method_info['end_line']):
                                    log_containing_methods_line[signature][file.split('/')[-1]].add(l)
        for signature in log_containing_methods_line:
            for file in log_containing_methods_line[signature]:
                log_containing_methods_line[signature][file] = sorted(list(log_containing_methods_line[signature][file]))
        with open(f"output/{self.project}_{self.registry}/static_analysis_log_containing_methods_line.json", "w") as f:
            json.dump(log_containing_methods_line, f, indent=4)


    def identify_log_containing_methods(self, application_log_manager: ApplicationLogManager):
        log_containing_methods_line = {}
        train_signatures, validation_signatures = get_train_test_split(self.project, self.registry, application_log_manager.get_signatures_including_logs())
        for signature in validation_signatures:
            if signature not in log_containing_methods_line:
                log_containing_methods_line[signature] = {}
            for thread_id, logs in application_log_manager.get_logs_by_signature(signature).items():
                for log in logs:
                    file = log.get_file()
                    line = int(log.get_line())
                    if file in self.class_method_info:
                        for method_info in self.class_method_info[file]["methods"]:
                            if method_info['start_line'] <= line <= method_info['end_line']:
                                print(f"Log: {log.get_log_statement()} is in Method: {method_info['class_name']}.{method_info['method_name']}")
                                if file.split('/')[-1] not in log_containing_methods_line[signature]:
                                    log_containing_methods_line[signature][file.split('/')[-1]] = set()
                                log_containing_methods_line[signature][file.split('/')[-1]].add(f"{method_info['class_name']}.{method_info['method_name']}")
        for signature in log_containing_methods_line:
            for file in log_containing_methods_line[signature]:
                log_containing_methods_line[signature][file] = sorted(list(log_containing_methods_line[signature][file]))
        with open(f"output/{self.project}_{self.registry}/static_analysis_log_containing_methods.json", "w") as f:
            json.dump(log_containing_methods_line, f, indent=4)


