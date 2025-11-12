from openai import OpenAI

class GPT:

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        self.client = OpenAI(api_key=self.api_key)

    def finetune(self, project, registry, model, level=""):
        file_path = f"output/{project}_{registry}/training.jsonl"
        if level == "method":
            file_path = f"output/{project}_{registry}/method_level_training.jsonl"
        elif level == "bulk":
            file_path = f"output/{project}_{registry}/bulk_training.jsonl"
        training_file = self.upload_file(file_path, "fine-tune")
        suffix = f"{project}_{registry}_model"
        response = self.client.fine_tuning.jobs.create(training_file=training_file.id, model=model, suffix=suffix)
        print(response)

    def batch_request(self, project, registry, level=''):
        file_path = f"output/{project}_{registry}/validation.jsonl"
        if level == "method":
            file_path = f"output/{project}_{registry}/method_level_validation.jsonl"
        elif level == "bulk":
            file_path = f"output/{project}_{registry}/bulk_validation.jsonl"
        validation_file = self.upload_file(file_path, "batch")
        response = self.client.batches.create(
            input_file_id=validation_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": f"Evaluation batch for {project}{registry}"
            }
        )
        print(response)

    def upload_file(self, file_path, purpose):
        return self.client.files.create(file=open(file_path, "rb"), purpose=purpose)
    
    def format_for_gpt_bulk_training(self, item):
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "Given application logs, provide estimated execution paths, where applicable: file name: executed lines|file name: executed lines"
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
    
    def format_for_gpt_bulk_validation(self, item, signature, id, model):
        return {
            "custom_id": f"{signature}-{id}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Given application logs, provide estimated execution paths, where applicable: file name: executed lines|file name: executed lines"
                    },
                    {
                        "role": "user",
                        "content": item
                    }
                ]
            }
        }



    def format_for_gpt_training(self, item):
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "Given two application logs, provide estimated execution paths between two logs, where applicable: executedclass.executedmethod | executedclass.executedmethod"
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

    def format_for_gpt_validation(self, item, signature, id, model):
        return {
            "custom_id": f"{signature}-{id}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Given two application logs, provide estimated execution paths between two logs, where applicable: executedclass.executedmethod | executedclass.executedmethod"
                    },
                    {
                        "role": "user",
                        "content": item
                    }
                ]
            }
        }