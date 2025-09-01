from openai import OpenAI

class GPT:

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        self.client = OpenAI(api_key=self.api_key)

    def finetune(self, project, registry, model):
        file_path = f"output/{project}_{registry}/training.jsonl"
        training_file = self.client.files.create(file=open(file_path, "rb"), purpose='fine-tune')
        suffix = f"{project}_{registry}_model"
        response = self.client.fine_tuning.jobs.create(training_file=training_file.id, model=model, suffix=suffix)
        print(response)


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

    def format_for_gpt_validation(self, item, signature, id):
        return {
            "custom_id": f"{signature}-{id}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Given two application logs, provide estimated execution paths between two logs, where applicable: file name: executed lines|file name: executed lines"
                    },
                    {
                        "role": "user",
                        "content": item
                    }
                ]
            }
        }