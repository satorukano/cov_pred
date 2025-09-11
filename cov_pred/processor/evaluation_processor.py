import json
from utils.evaluation import evaluate, format, evaluate_methods_level
from utils.format_util import merge_traces, string_traces, set_methods

class EvaluationProcessor:

    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry

    def evaluate(self):
        # Implement evaluation logic here
        pred_file = f"output/{self.project}_{self.registry}/validation_prediction.jsonl"
        with open(pred_file, "r") as f:
            raw_predictions = [json.loads(line) for line in f.readlines()]
        ans_file = f"output/{self.project}_{self.registry}/validation_oracle.json"
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
            precision, recall = evaluate(pred, ans)
            results[signature] = {"precision": precision, "recall": recall, "f1": (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0}
        results["average"] = {
            "precision": sum(result["precision"] for result in results.values()) / len(results),
            "recall": sum(result["recall"] for result in results.values()) / len(results),
            "f1": sum(result["f1"] for result in results.values()) / len(results),
        }
        with open(f"output/{self.project}_{self.registry}/validation_metrics.json", "w") as f:
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
