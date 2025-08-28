from sklearn.model_selection import train_test_split
import json
import os

class FormatProcessor:

    def __init__(self, test_percentage=0.2, log_count_threshold=1):
        self.test_percentage = test_percentage
        self.log_count_threshold = log_count_threshold

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
        data_for_gpt = []
        for signature, threads_collection in formatted_collection.items():
            content = {signature: []}
            container = []
            for thread_id, items in threads_collection.items():
                container.append([self.format_for_gpt_training(item) for item in items])
            content[signature] = container
            data_for_gpt.append(content)
        print(f"Total data for GPT: {len(data_for_gpt)}")
        train, test = train_test_split(data_for_gpt, test_size=self.test_percentage, random_state=42)
        self.make_training_jsonl(train, f"output/{project}_{registry}/training.jsonl")

        return formatted_collection
    
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
    
    def format_for_gpt_training(self, item):
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "Given two application logs, provide estimated execution paths between two logs, where applicable: file name: executed lines|file name: executed lines"
                },
                {
                    "role": "user",
                    "content": list(item.keys())[0]
                },
                {
                    "role": "assistant",
                    "content": list(item.values())[0]
                }
            ]
        }
    
    def make_training_jsonl(self, training_data, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            for item in training_data:
                for value in item.values():
                    if len(value) == 0:
                        continue
                    for train in value[0]:
                        f.write(json.dumps(train) + "\n")