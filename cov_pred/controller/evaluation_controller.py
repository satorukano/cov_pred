from processor.evaluation_processor import EvaluationProcessor
from utils.git import Git
from database import Database

class EvaluationController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        self.evaluation_processor = EvaluationProcessor(self.project, self.registry)
    
    def setup(self):
        self.evaluation_processor = EvaluationProcessor(self.project, self.registry)

    def evaluate(self):
        self.evaluation_processor.evaluate()
    
    def method_level_evaluate(self):
        self.evaluation_processor.method_level_evaluate()
    
    def logcoco_method_level_evaluate(self):
        db = Database()
        git = Git(self.project, self.registry, "./repos", db)
        git.clone_or_checkout_commit()
        self.evaluation_processor.logcoco_method_level_evaluate()