from dotenv import load_dotenv
load_dotenv()
from utils.gpt import GPT

import os

class GPTController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.gpt = GPT(self.api_key)
    
    def finetune(self, model="gpt-4.1-mini-2025-04-14", method_level=False):
        self.gpt.finetune(self.project, self.registry, model)

    def method_level_finetune(self, model="gpt-4.1-mini-2025-04-14", method_level=True):
        self.gpt.finetune(self.project, self.registry, model, method_level)
    
    def batch_request(self):
        self.gpt.batch_request(self.project, self.registry)

    def method_level_batch_request(self):
        self.gpt.batch_request(self.project, self.registry, method_level=True)
