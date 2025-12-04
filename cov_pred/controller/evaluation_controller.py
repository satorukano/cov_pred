from processor.evaluation_processor import EvaluationProcessor
from utils.git import Git
from utils.java_util import extract_empty_and_comment_lines
from database import Database

class EvaluationController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        self.empty_and_comment_lines = extract_empty_and_comment_lines(f"./repos/{self.project}")
        self.evaluation_processor = EvaluationProcessor(self.project, self.registry, self.empty_and_comment_lines)

    def evaluate(self, bulk: bool = False):
        self.evaluation_processor.evaluate(bulk=bulk)

    def logcoco_evaluate(self):
        self.evaluation_processor.logcoco_evaluate()
    
    def static_line_evaluate(self):
        self.evaluation_processor.static_line_evaluate()
    
    def method_level_evaluate(self):
        self.evaluation_processor.method_level_evaluate()
    
    def method_level_from_line_evaluate(self):
        self.evaluation_processor.method_level_from_line_evaluate()
    
    def static_method_level_evaluate(self):
        self.evaluation_processor.static_method_level_evaluate()
    
    def logcoco_method_level_evaluate(self):
        db = Database()
        git = Git(self.project, self.registry, "./repos", db)
        git.clone_or_checkout_commit()
        self.evaluation_processor.logcoco_method_level_evaluate()