from sklearn.model_selection import train_test_split
from utils.gpt import GPT
import json
import os
from controller.application_log_controller import ApplicationLogController
from controller.trace_controller import TraceController

class FormatProcessor:

    def __init__(self, signatures_including_logs: list[str], gpt: GPT, test_percentage=0.2, log_count_threshold=1):
        self.test_percentage = test_percentage
        self.log_count_threshold = log_count_threshold
        self.signatures_including_logs = signatures_including_logs
        self.gpt = gpt
        self.validation_signatures = []

    def format_for_training(self, collection, project, registry):
        formatted_collection = {}
        for signature, threads_collection in collection.items():
            formatted_collection[signature] = {}
            for thread_id, logs_executions in threads_collection.items():
                formatted_collection[signature][thread_id] = []
                count = 0
                logs = []
                merged_traces = {}

                for (prev_log, curr_log), executions in logs_executions.items():
                    count += 1
                    traces = self.extract_file_line_from_traces(executions)
                    previous_statement = prev_log.get_log_statement() if prev_log != "" else ""
                    current_statement = curr_log.get_log_statement() if curr_log != "" else ""
                    if len(previous_statement) > 2000 or len(current_statement) > 2000:
                        count -= 1
                        continue
                    formatted_previous_log = self.cut_prefix(previous_statement, "START")
                    formatted_current_log = self.cut_prefix(current_statement, "END")


                    if count == 1:
                        logs.append(formatted_previous_log)
                    logs.append(formatted_current_log)
                    merged_traces = self.merge_traces(merged_traces, traces)
                    if count == len(logs_executions.keys()):
                        formatted_collection[signature][thread_id].append({
                            f'{"|||".join(logs)}': self.string_traces(merged_traces)
                        })
                    if count == self.log_count_threshold:
                        formatted_collection[signature][thread_id].append({
                            f'{"|||".join(logs)}': self.string_traces(merged_traces)
                        })
                        count = 0
                        logs = []
                        merged_traces = {}
        train_signature, validation_signature = train_test_split(self.signatures_including_logs, test_size=self.test_percentage, random_state=42)
        training_data = []
        self.validation_signatures = validation_signature
        for signature, threads_collection in formatted_collection.items():
            for thread_id, items in threads_collection.items():
                if signature in train_signature:
                    training_data.extend(self.gpt.format_for_gpt_training(item) for item in items)
        self.make_jsonl(training_data, f"output/{project}_{registry}/training.jsonl")

    def format_for_validation(self, application_log_controller: ApplicationLogController, project: str, registry: str):
        validation_input = []
        for signature in self.validation_signatures:
            id_for_validation = 0
            for thread_id, logs in application_log_controller.get_logs_by_signature(signature).items():
                previous_log = ""
                current_log = ""
                log_count =0
                while log_count <= len(logs):
                    if log_count == len(logs):
                        input_data = f"{previous_log}|||END"
                        validation_input.append(self.gpt.format_for_gpt_validation(input_data, signature, id_for_validation))
                        break

                    if log_count == 0:
                        previous_log = "START"
                    current_log = logs[log_count]
                    input_current_statement = self.cut_prefix(current_log.get_log_statement(), "END")
                    input_data = f"{previous_log}|||{input_current_statement}"
                    validation_input.append(self.gpt.format_for_gpt_validation(input_data, signature, id_for_validation))
                    id_for_validation += 1
                    previous_log = input_current_statement
                    log_count += 1
        self.make_jsonl(validation_input, f"output/{project}_{registry}/validation.jsonl")
    
    def make_validation_oracle(self, trace_controller: TraceController, project: str, registry: str):
        oracle = {}
        for signature in self.validation_signatures:
            oracle[signature] = {}
            for thread_id, traces in trace_controller.get_traces_by_signature(signature).items():
                file_line = self.extract_file_line_from_traces(traces)
                oracle[signature] = self.merge_traces(oracle[signature], file_line)
            oracle[signature] = self.string_traces(oracle[signature])
        with open(f"output/{project}_{registry}/validation_oracle.json", "w") as f:
            json.dump(oracle, f, indent=4)


    def cut_prefix(self, log_statement: str, default: str) -> str:
        log_levels = ['INFO', 'DEBUG', 'WARN', 'ERROR']
        for level in log_levels:
            if level in log_statement:
                log_level_index = log_statement.find(level)
                return log_statement[log_level_index:].strip()
        return default
    
    def extract_file_line_from_traces(self, traces: list) -> dict[str, list[int]]:
        result = {}
        for trace in traces:
            file = trace.get_file().split("/")[-1]
            line = int(trace.get_line())
            if file not in result:
                result[file] = []
            if line not in result[file]:
                result[file].append(line)
        for file, lines in result.items():
            result[file] = sorted(lines)
        return result
    
    def merge_traces(self, traces1: dict[str, list[int]], traces2: dict[str, list[int]]) -> dict[str, list[int]]:
        merged = traces1.copy()
        for file, lines in traces2.items():
            if file not in merged:
                merged[file] = lines
            else:
                for line in lines:
                    if line not in merged[file]:
                        merged[file].append(line)
                merged[file] = sorted(merged[file])
        return merged
    
    def string_traces(self, traces: dict[str, list[int]]) -> str:
        result = []
        for file, lines in traces.items():
            lines_str = ",".join([str(line) for line in lines])
            result.append(f"{file}:{lines_str}")
        return " | ".join(result)
    
    def make_jsonl(self, data, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")