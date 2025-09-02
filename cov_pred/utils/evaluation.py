import json
import os

def evaluate(pred, ans):
    formatted_pred = format(pred)
    formatted_ans = format(ans)
    precision = calc_precision(formatted_pred, formatted_ans)
    recall = calc_recall(formatted_pred, formatted_ans)
    return precision, recall

def format(data):
    formatted = {}
    for file_line in data.split("|"):
        if ":" not in file_line:
            continue
        if len(file_line.split(":")) != 2:
            continue
        file_name, lines = file_line.split(":")
        int_lines = []
        for line in lines.split(","):
            try:
                if "-" in line:
                    start, end = line.split("-")
                    for i in range(int(start), int(end)+1):
                        int_lines.append(i)
                else:
                    int_lines.append(int(line))
            except:
                continue
        if file_name in formatted:
            formatted[file_name].extend(int_lines)
            formatted[file_name] = list(set(formatted[file_name]))
        else:
            formatted[file_name] = int_lines
    return formatted

def calc_recall(formatted_pred, formatted_ans):
    all_lines = 0
    right_pred = 0
    for ans_file_name, ans_lines in formatted_ans.items():
        if ans_file_name in formatted_pred.keys():
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
        if pred_file_name in formatted_ans.keys():
            for pred_line in pred_lines:
                if pred_line in formatted_ans[pred_file_name]:
                    right_pred+=1
                all_lines+=1
        else:
            all_lines += len(pred_lines)
    if all_lines == 0:
        return 0
    return right_pred / all_lines
