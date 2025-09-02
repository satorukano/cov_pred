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
        lines_str = ",".join([str(line) for line in lines])
        result.append(f"{file}:{lines_str}")
    return " | ".join(result)

def cut_prefix(self, log_statement: str, default: str) -> str:
    log_levels = ['INFO', 'DEBUG', 'WARN', 'ERROR']
    for level in log_levels:
        if level in log_statement:
            log_level_index = log_statement.find(level)
            return log_statement[log_level_index:].strip()
    return default

def extract_file_line_from_traces(self, traces: list, empty_and_comment_lines: dict[str, list[int]]) -> dict[str, list[int]]:
    result = {}
    for trace in traces:
        file = trace.get_file().split("/")[-1]
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
        result[file] = sorted(list(set(sorted_lines)))
    return result