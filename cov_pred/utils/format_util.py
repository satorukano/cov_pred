import os
import json
from ordered_set import OrderedSet
import pathlib
from sklearn.model_selection import train_test_split

def merge_traces(traces1: dict[str, list[int]], traces2: dict[str, list[int]]) -> dict[str, list[int]]:
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

def string_traces(traces: dict[str, list[int]]) -> str:
    result = []
    for file, lines in traces.items():
        line_count = 0
        file_line = []
        while line_count < len(lines):
            start_line = lines[line_count]
            end_line = lines[line_count]
            while line_count + 1 < len(lines) and end_line + 1 == lines[line_count + 1]:
                end_line = lines[line_count + 1]
                line_count += 1
            if start_line == end_line:
                line_count += 1
                file_line.append(f"{start_line}")
            else:
                line_count += 1
                file_line.append(f"{start_line}-{end_line}")
        result.append(f"{file}:{','.join(file_line)}")
    return " | ".join(result)

def cut_prefix(log_statement: str, default: str) -> str:
    log_levels = ['INFO', 'DEBUG', 'WARN', 'ERROR']
    for level in log_levels:
        if level in log_statement:
            log_level_index = log_statement.find(level)
            return log_statement[log_level_index:].strip()
    return default

def extract_file_line_from_traces(traces: list, empty_and_comment_lines: dict[str, list[int]]) -> dict[str, list[int]]:
    result = {}
    return_result = {}
    for trace in traces:
        file = trace.get_file()
        line = int(trace.get_line())
        if file not in result:
            result[file] = []
        if line not in result[file]:
            result[file].append(line)
    for file, lines in result.items():
        sorted_lines = sorted(lines)
        for i in range(len(sorted_lines)-1):
            empty_lines = empty_and_comment_lines.get(file, [])
            add = True
            added_lines = []
            for j in range(sorted_lines[i]+1, sorted_lines[i+1]):
                if j not in empty_lines:
                    add = False
                    break
                added_lines.append(j)
            if add:
                sorted_lines.extend(added_lines)
        return_result[file.split("/")[-1]] = sorted(list(set(sorted_lines)))
    return return_result

def extract_method_from_traces(traces: list, class_method_info: dict[list[dict[str, str]]]):
    result = OrderedSet()
    for trace in traces:
        file = trace.get_file()
        line = int(trace.get_line())
        if file in class_method_info:
            for method_info in class_method_info[file]["methods"]:
                if method_info['start_line'] <= line <= method_info['end_line']:
                    result.add(method_info["class_name"] + "." + method_info["method_name"])
    return result

def string_methods(methods: set[str]) -> str:
    return " | ".join(list(methods))

def make_jsonl(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

def set_methods(methods: str) -> set[str]:
    return set(map(str.strip, methods.split("|")))

def get_train_test_split(project: str, registry: str, signatures: list[str], test_size=0.2, random_state=42):
    file_path = pathlib.Path(f"output/{project}_{registry}/train_test_signature.json")
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
            return data["train"], data["test"]
    train, test = train_test_split(signatures, test_size=test_size, random_state=random_state)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump({"train": train, "test": test}, f)
    return train, test