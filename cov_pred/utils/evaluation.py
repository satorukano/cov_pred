import json
import os

def evaluate(pred, ans, empty_and_comment_lines=None):
    print("pred")
    formatted_pred = format(pred, empty_and_comment_lines)
    print("ans")
    formatted_ans = format(ans, empty_and_comment_lines)
    precision = calc_precision(formatted_pred, formatted_ans)
    recall = calc_recall(formatted_pred, formatted_ans)
    return precision, recall

def format(data, empty_and_comment_lines={}):
    formatted = {}
    file_empty_comment_lines = {}
    for file_name, lines in empty_and_comment_lines.items():
        file_empty_comment_lines[file_name.split('/')[-1]] = lines

    for file_line in data.split("|"):
        if ":" not in file_line:
            continue
        if len(file_line.split(":")) != 2:
            continue
        file_name, lines = file_line.split(":")
        file_name = file_name.strip()
        empty_and_comment_line = file_empty_comment_lines.get(file_name, [])
        int_lines = []
        for line in lines.split(","):
            try:
                if "-" in line:
                    start, end = line.split("-")
                    if int(end) > 100000:
                        continue
                    for i in range(int(start), int(end)+1):
                        if i in empty_and_comment_line:
                            continue
                        int_lines.append(i)
                else:
                    if int(line) in empty_and_comment_line:
                        continue
                    int_lines.append(int(line))
            except:
                continue
        if file_name in formatted:
            formatted[file_name].extend(int_lines)
            formatted[file_name] = list(set(formatted[file_name]))
        else:
            formatted[file_name] = int_lines
    print(formatted)
    return formatted

def calc_recall(formatted_pred, formatted_ans):
    all_lines = 0
    right_pred = 0
    for ans_file_name, ans_lines in formatted_ans.items():
        if ans_file_name in formatted_pred:
            for ans_line in ans_lines:
                if ans_line in formatted_pred[ans_file_name]:
                    right_pred+=1
                all_lines+=1
        else:
            all_lines += len(ans_lines)
    if all_lines == 0:
        return 0
    return right_pred / all_lines

def calc_precision(formatted_pred, formatted_ans):
    all_lines = 0
    right_pred = 0
    for pred_file_name, pred_lines in formatted_pred.items():
        if pred_file_name in formatted_ans:
            for pred_line in pred_lines:
                if pred_line in formatted_ans[pred_file_name]:
                    right_pred+=1
                all_lines+=1
        else:
            all_lines += len(pred_lines)
    if all_lines == 0:
        return 0
    return right_pred / all_lines

def evaluate_methods_level(pred, ans):
    pred_set = set(pred)
    ans_set = set(ans)
    if len(pred_set) == 0:
        precision = 0
    else:
        precision = len(pred_set & ans_set) / len(pred_set)
    
    if len(ans_set) == 0:
        recall = 0
    else:
        recall = len(pred_set & ans_set) / len(ans_set)
    
    return precision, recall
