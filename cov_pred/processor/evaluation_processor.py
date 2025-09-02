import json
from utils.evaluation import evaluate, format
from utils.format_util import merge_traces, string_traces

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
