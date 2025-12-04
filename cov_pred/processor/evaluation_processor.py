import json
import os
import csv
from utils.evaluation import evaluate, format, evaluate_methods_level
from utils.format_util import merge_traces, string_traces, set_methods
from utils.java_util import extract_all_class_and_method_info
from manager.application_log_manager import ApplicationLogManager

class EvaluationProcessor:

    def __init__(self, project: str, registry: str, empty_and_comment_lines: dict[str, list[int]]):
        self.project = project
        self.registry = registry
        self.empty_and_comment_lines = empty_and_comment_lines

    def evaluate(self, bulk: bool = False):
        # Implement evaluation logic here
        pred_file = f"output/{self.project}_{self.registry}/validation_prediction.jsonl"
        if bulk:
            pred_file = f"output/{self.project}_{self.registry}/bulk_validation_prediction.jsonl"
        with open(pred_file, "r") as f:
            raw_predictions = [json.loads(line) for line in f.readlines()]
        ans_file = f"output/{self.project}_{self.registry}/validation_oracle.json"
        if bulk:
            ans_file = f"output/{self.project}_{self.registry}/bulk_validation_oracle.json"
        with open(ans_file, "r") as f:
            answers = json.load(f)
        predictions = {}
        for prediction in raw_predictions:
            signature = prediction["custom_id"].split("#")[0] + '#'
            if signature not in predictions:
                predictions[signature] = {}
            predictions[signature] = merge_traces(predictions[signature], format(prediction["response"]["body"]["choices"][0]["message"]["content"]))

        results = {}
        for signature in predictions.keys():
            ans = answers.get(signature, "")
            pred = string_traces(predictions[signature])
            precision, recall = evaluate(pred, ans, self.empty_and_comment_lines)
            results[signature] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        results["average"] = {
            "precision": sum(result["precision"] for result in results.values()) / len(results),
            "recall": sum(result["recall"] for result in results.values()) / len(results),
            "f1": sum(result["f1"] for result in results.values()) / len(results),
        }
        with open(f"output/{self.project}_{self.registry}/validation_metrics.json", "w") as f:
            json.dump(results, f, indent=4)
    
    def logcoco_evaluate(self, include_may_lines: bool = False):
        logcoco_results_directory = f"LogCoCo/{self.project}_{self.registry}"
        evaluation_results = {}
        predictions = {}
        oracle = {}
        oracle_file = f"output/{self.project}_{self.registry}/bulk_validation_oracle.json"
        with open(oracle_file, "r") as f:
            oracle = json.load(f)
        formatted_oracle = {}
        for method, ans in oracle.items():
            formatted_oracle[method.split(";")[-1]] = ans
        for dir in os.listdir(logcoco_results_directory):
            test_method_name = dir
            predictions[test_method_name] = {}
            with open(f"{logcoco_results_directory}/{test_method_name}/coverage.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["MustCoveredLines"] == "0":
                        continue
                    # Get the relative file path(TODO fix for your environment)
                    file = os.path.relpath(row["FilePath"], "/work/satoru-k/projects/"+self.project).split('/')[-1]
                    must_lines = row['MustLineNumbers']
                    may_lines = row['MayLineNumbers'] if include_may_lines else None
                    lines = must_lines.split(";")
                    if may_lines and may_lines != 'None':
                        lines += may_lines.split(";")
                    for line in lines:
                        line_number = int(line)
                        if file not in predictions[test_method_name]:
                            predictions[test_method_name][file] = []
                        predictions[test_method_name][file].append(line_number)
            
            for file, lines in predictions[test_method_name].items():
                predictions[test_method_name][file] = sorted(list(set(lines)))
            oracle = formatted_oracle.get(test_method_name, "")
            pred = string_traces(predictions.get(test_method_name, {}))
            precision, recall = evaluate(pred, oracle, self.empty_and_comment_lines)
            evaluation_results[test_method_name] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        evaluation_results["average"] = {
            "precision": sum(result["precision"] for result in evaluation_results.values()) / len(evaluation_results),
            "recall": sum(result["recall"] for result in evaluation_results.values()) / len(evaluation_results),
            "f1": sum(result["f1"] for result in evaluation_results.values()) / len(evaluation_results),
        }
        with open(f"output/{self.project}_{self.registry}/logcoco_validation_metrics.json", "w") as f:
            json.dump(evaluation_results, f, indent=4)
    
    def static_line_evaluate(self):
        pred_file = f"output/{self.project}_{self.registry}/static_analysis_log_containing_methods_line.json"
        with open(pred_file, "r") as f:
            predictions = json.load(f)
        ans_file = f"output/{self.project}_{self.registry}/bulk_validation_oracle.json"
        with open(ans_file, "r") as f:
            answers = json.load(f)
        results = {}
        for signature in predictions.keys():
            ans = answers.get(signature, "")
            pred = string_traces(predictions[signature])
            precision, recall = evaluate(pred, ans, self.empty_and_comment_lines)
            results[signature] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        # results["average"] = {
        #     "precision": sum(result["precision"] for result in results.values()) / len(results),
        #     "recall": sum(result["recall"] for result in results.values()) / len(results),
        #     "f1": sum(result["f1"] for result in results.values()) / len(results),
        # }
        with open(f"output/{self.project}_{self.registry}/static_line_validation_metrics.json", "w") as f:
            json.dump(results, f, indent=4)

    def method_level_evaluate(self):
        # Implement evaluation logic here
        pred_file = f"output/{self.project}_{self.registry}/method_level_validation_prediction.jsonl"
        with open(pred_file, "r") as f:
            raw_predictions = [json.loads(line) for line in f.readlines()]
        ans_file = f"output/{self.project}_{self.registry}/method_level_validation_oracle.json"
        with open(ans_file, "r") as f:
            answers = json.load(f)
        predictions = {}
        for prediction in raw_predictions:
            signature = prediction["custom_id"].split("#")[0] + '#'
            if signature not in predictions:
                predictions[signature] = set()
            predictions[signature].update(set_methods(prediction["response"]["body"]["choices"][0]["message"]["content"]))

        results = {}
        for signature in predictions.keys():
            ans = set_methods(answers.get(signature, ""))
            pred = predictions[signature]
            precision, recall = evaluate_methods_level(pred, ans)
            results[signature] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        results["average"] = {
            "precision": sum(result["precision"] for result in results.values()) / len(results),
            "recall": sum(result["recall"] for result in results.values()) / len(results),
            "f1": sum(result["f1"] for result in results.values()) / len(results),
        }
        with open(f"output/{self.project}_{self.registry}/method_level_validation_metrics.json", "w") as f:
            json.dump(results, f, indent=4)
    
    def method_level_from_line_evaluate(self):
        # Load class and method info
        class_and_method_info = extract_all_class_and_method_info(f"repos/{self.project}")

        # Load line-level predictions
        pred_file = f"output/{self.project}_{self.registry}/validation_prediction.jsonl"
        with open(pred_file, "r") as f:
            raw_predictions = [json.loads(line) for line in f.readlines()]

        # Load method-level oracle
        ans_file = f"output/{self.project}_{self.registry}/method_level_validation_oracle.json"
        with open(ans_file, "r") as f:
            answers = json.load(f)

        # Convert line-level predictions to method-level predictions
        # First, merge all predictions for each signature
        line_predictions = {}
        for prediction in raw_predictions:
            signature = prediction["custom_id"].split("#")[0] + '#'
            if signature not in line_predictions:
                line_predictions[signature] = {}
            line_predictions[signature] = merge_traces(
                line_predictions[signature],
                format(prediction["response"]["body"]["choices"][0]["message"]["content"], self.empty_and_comment_lines)
            )

        # Convert merged line-level predictions to method-level
        predictions = {}
        for signature, line_prediction in line_predictions.items():
            predictions[signature] = set()

            # For each file and its lines in the prediction
            for file_name, lines in line_prediction.items():
                # Find the corresponding file in class_and_method_info
                matched_file = None
                for file_path, file_info in class_and_method_info.items():
                    if file_path.endswith(file_name):
                        matched_file = file_path
                        break

                if matched_file is None:
                    continue

                file_info = class_and_method_info[matched_file]
                methods_info = file_info.get("methods", [])

                # For each line, find which method it belongs to
                for line in lines:
                    for method_info in methods_info:
                        if method_info['start_line'] <= line <= method_info['end_line']:
                            method_full_name = method_info["class_name"] + "." + method_info["method_name"]
                            predictions[signature].add(method_full_name)
                            break

        # Evaluate method-level predictions
        results = {}
        for signature in predictions.keys():
            ans = set_methods(answers.get(signature, ""))
            pred = predictions[signature]
            precision, recall = evaluate_methods_level(pred, ans)
            results[signature] = {
                "precision": precision,
                "recall": recall,
                "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            }

        results["average"] = {
            "precision": sum(result["precision"] for result in results.values()) / len(results) if len(results) > 0 else 0,
            "recall": sum(result["recall"] for result in results.values()) / len(results) if len(results) > 0 else 0,
            "f1": sum(result["f1"] for result in results.values()) / len(results) if len(results) > 0 else 0,
        }

        # Save results
        with open(f"output/{self.project}_{self.registry}/method_level_from_line_validation_metrics.json", "w") as f:
            json.dump(results, f, indent=4)

    def static_method_level_evaluate(self):
        # Implement evaluation logic here
        pred_file = f"output/{self.project}_{self.registry}/static_analysis_log_containing_methods.json"
        with open(pred_file, "r") as f:
            predictions = json.load(f)
        ans_file = f"output/{self.project}_{self.registry}/method_level_validation_oracle.json"
        with open(ans_file, "r") as f:
            answers = json.load(f)
        results = {}
        for signature, prediction in predictions.items():
            ans = set_methods(answers.get(signature, ""))
            pred = []
            for file, methods in prediction.items():
                pred.extend(methods)
            precision, recall = evaluate_methods_level(pred, ans)
            results[signature] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        results["average"] = {
            "precision": sum(result["precision"] for result in results.values()) / len(results),
            "recall": sum(result["recall"] for result in results.values()) / len(results),
            "f1": sum(result["f1"] for result in results.values()) / len(results),
        }
        with open(f"output/{self.project}_{self.registry}/static_method_level_validation_metrics.json", "w") as f:
            json.dump(results, f, indent=4)
    
    def logcoco_method_level_evaluate(self):
        logcoco_results_directory = f"LogCoCo/{self.project}_{self.registry}"
        evaluation_results = {}
        class_and_method_info = extract_all_class_and_method_info(f"repos/{self.project}")
        oracle = {}
        oracle_file = f"output/{self.project}_{self.registry}/method_level_validation_oracle.json"
        with open(oracle_file, "r") as f:
            oracle = json.load(f)
        formatted_oracle = {}
        for method, ans in oracle.items():
            formatted_oracle[method.split(";")[-1]] = ans
        for dir in os.listdir(logcoco_results_directory):
            test_method_name = dir
            executed_method = set()
            with open(f"{logcoco_results_directory}/{test_method_name}/coverage.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["MustCoveredLines"] == "0":
                        continue
                    # Get the relative file path(TODO fix for your environment)
                    file_path = os.path.relpath(row["FilePath"], "/work/satoru-k/projects/"+self.project)
                    method_name = row["Method"]
                    file_info = class_and_method_info.get(file_path, {})

                    if not file_info:
                        continue
                    methods_info = file_info.get("methods", [])
                    for method_info in methods_info:
                        if method_info["method_name"] == method_name and int(row["StartLine"]) <= method_info["start_line"] and method_info["end_line"] <= int(row["EndLine"]):
                            executed_method.add(method_info["class_name"] + "." + method_info["method_name"])
                oracle_methods = set_methods(formatted_oracle.get(test_method_name, ""))
                precision, recall = evaluate_methods_level(executed_method, oracle_methods)
                evaluation_results[test_method_name] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
            evaluation_results["average"] = {
                "precision": sum(result["precision"] for result in evaluation_results.values()) / len(evaluation_results),
                "recall": sum(result["recall"] for result in evaluation_results.values()) / len(evaluation_results),
                "f1": sum(result["f1"] for result in evaluation_results.values()) / len(evaluation_results),
            }
        with open(f"output/{self.project}_{self.registry}/logcoco_method_level_validation_metrics.json", "w") as f:
            json.dump(evaluation_results, f, indent=4)


