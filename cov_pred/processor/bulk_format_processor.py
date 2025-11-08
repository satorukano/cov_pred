from sklearn.model_selection import train_test_split
from utils.gpt import GPT
from utils.format_util import merge_traces, string_traces, extract_file_line_from_traces, cut_prefix, make_jsonl, get_train_test_split
import json
import os
from manager.application_log_manager import ApplicationLogManager
from manager.trace_manager import TraceManager


class BulkFormatProcessor:

    def __init__(self, project: str, registry: str, signatures_including_logs: list[str], gpt: GPT, empty_and_comment_lines: dict[str, list[int]], application_log_manager: ApplicationLogManager, trace_manager: TraceManager, test_percentage=0.2, log_count_threshold=1):
        self.project = project
        self.registry = registry
        self.test_percentage = test_percentage
        self.log_count_threshold = log_count_threshold
        self.signatures_including_logs = signatures_including_logs
        self.gpt = gpt
        self.empty_and_comment_lines = empty_and_comment_lines
        self.application_log_manager = application_log_manager
        self.trace_manager = trace_manager
        self.training_signatures, self.validation_signatures = get_train_test_split(self.project, self.registry, self.signatures_including_logs, test_size=self.test_percentage, random_state=42)

    def format_for_training(self, collection):
        datasets = {}
        training_dataset = {}
        for signature in self.signatures_including_logs:
            datasets[signature] = {}
            logs = self.application_log_manager.get_logs_by_signature(signature)
            total_logs = []
            for thread_id, log_list in logs.items():
                total_logs.extend([log.get_log_statement() for log in log_list])
            logs_str = "|".join(total_logs)
            for thread_id, traces in self.trace_manager.get_traces_by_signature(signature).items():
                file_line = extract_file_line_from_traces(traces, self.empty_and_comment_lines)
                datasets[signature] = merge_traces(datasets[signature], file_line)
            datasets[signature] = string_traces(datasets[signature])
            training_dataset[signature] = {logs_str: datasets[signature]}

        
        training_data = []
        for signature, item in training_dataset.items():
            if signature in self.training_signatures:
                training_data.append(self.gpt.format_for_gpt_bulk_training(item))
        make_jsonl(training_data, f"output/{self.project}_{self.registry}/bulk_training.jsonl")

    def format_for_validation(self, application_log_manager: ApplicationLogManager, model: str):
        validation_input = []
        for signature in self.validation_signatures:
            if signature == '':
                print("Empty signature found in validation signatures.")
            id_for_validation = 0
            total_logs = []
            for thread_id, logs in application_log_manager.get_logs_by_signature(signature).items():
                total_logs.extend([log.get_log_statement() for log in logs])
                input_data = "|".join(total_logs)
            validation_input.append(self.gpt.format_for_gpt_bulk_validation(input_data, signature, id_for_validation, model))
        make_jsonl(validation_input, f"output/{self.project}_{self.registry}/bulk_validation.jsonl")

    def make_validation_oracle(self, trace_manager: TraceManager):
        oracle = {}
        for signature in self.validation_signatures:
            oracle[signature] = {}
            for thread_id, traces in trace_manager.get_traces_by_signature(signature).items():
                file_line = extract_file_line_from_traces(traces, self.empty_and_comment_lines)
                oracle[signature] = merge_traces(oracle[signature], file_line)
            oracle[signature] = string_traces(oracle[signature])
        with open(f"output/{self.project}_{self.registry}/bulk_validation_oracle.json", "w") as f:
            json.dump(oracle, f, indent=4)