from sklearn.model_selection import train_test_split
from utils.java_util import extract_class_and_method_info
from utils.gpt import GPT
from utils.format_util import string_methods, extract_method_from_traces, cut_prefix, make_jsonl, get_train_test_split
from manager.application_log_manager import ApplicationLogManager
from manager.trace_manager import TraceManager
from ordered_set import OrderedSet
import json

class MethodLevelFormatProcessor:
    def __init__(self, project: str, registry: str, signatures_including_logs: list[str], gpt: GPT, class_method_info, test_percentage=0.2, log_count_threshold=1):
        self.project = project
        self.registry = registry
        self.test_percentage = test_percentage
        self.log_count_threshold = log_count_threshold
        self.signatures_including_logs = signatures_including_logs
        self.gpt = gpt
        self.class_method_info = class_method_info
        self.training_signatures, self.validation_signatures = get_train_test_split(self.project, self.registry,self.signatures_including_logs, test_size=self.test_percentage, random_state=42)

    def format_for_training(self, collection):
        formatted_collection = {}
        for signature, threads_collection in collection.items():
            formatted_collection[signature] = {}
            for thread_id, logs_executions in threads_collection.items():
                formatted_collection[signature][thread_id] = []
                count = 0
                logs = []
                total_methods = OrderedSet()

                for (prev_log, curr_log), executions in logs_executions.items():
                    count += 1
                    methods = extract_method_from_traces(executions, self.class_method_info)
                    previous_statement = prev_log.get_log_statement() if prev_log != "" else ""
                    current_statement = curr_log.get_log_statement() if curr_log != "" else ""
                    if len(previous_statement) > 2000 or len(current_statement) > 2000:
                        count -= 1
                        continue
                    formatted_previous_log = cut_prefix(previous_statement, "START")
                    formatted_current_log = cut_prefix(current_statement, "END")


                    if count == 1:
                        logs.append(formatted_previous_log)
                    logs.append(formatted_current_log)
                    total_methods.update(methods)
                    if count == len(logs_executions.keys()):
                        formatted_collection[signature][thread_id].append({
                            f'{"|||".join(logs)}': string_methods(total_methods)
                        })
                    if count == self.log_count_threshold:
                        formatted_collection[signature][thread_id].append({
                            f'{"|||".join(logs)}': string_methods(total_methods)
                        })
                        count = 0
                        logs = []
                        total_methods = OrderedSet()
        training_data = []
        for signature, threads_collection in formatted_collection.items():
            for thread_id, items in threads_collection.items():
                if signature in self.training_signatures:
                    training_data.extend(self.gpt.format_for_gpt_training(item) for item in items)
        make_jsonl(training_data, f"output/{self.project}_{self.registry}/method_level_training.jsonl")

    def format_for_validation(self, application_log_manager: ApplicationLogManager, model: str):
        validation_input = []
        for signature in self.validation_signatures:
            id_for_validation = 0
            for thread_id, logs in application_log_manager.get_logs_by_signature(signature).items():
                previous_log = ""
                current_log = ""
                log_count =0
                while log_count <= len(logs):
                    id_for_validation += 1
                    if log_count == len(logs):
                        input_data = f"{previous_log}|||END"
                        validation_input.append(self.gpt.format_for_gpt_validation(input_data, signature, id_for_validation, model))
                        break

                    if log_count == 0:
                        previous_log = "START"
                    current_log = logs[log_count]
                    input_current_statement = cut_prefix(current_log.get_log_statement(), "END")
                    input_data = f"{previous_log}|||{input_current_statement}"
                    validation_input.append(self.gpt.format_for_gpt_validation(input_data, signature, id_for_validation, model))
                    previous_log = input_current_statement
                    log_count += 1
        make_jsonl(validation_input, f"output/{self.project}_{self.registry}/method_level_validation.jsonl")

    def make_validation_oracle(self, trace_manager: TraceManager):
        oracle = {}
        for signature in self.validation_signatures:
            oracle[signature] = set()
            for thread_id, traces in trace_manager.get_traces_by_signature(signature).items():
                methods = extract_method_from_traces(traces, self.class_method_info)
                oracle[signature].update(methods)
            oracle[signature] = string_methods(oracle[signature])
        with open(f"output/{self.project}_{self.registry}/method_level_validation_oracle.json", "w") as f:
            json.dump(oracle, f, indent=4)