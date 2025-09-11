from processor.evaluation_processor import EvaluationProcessor

class EvaluationController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        self.evaluation_processor = EvaluationProcessor(self.project, self.registry)
    
    def setup_for_line_level(self):
        self.evaluation_processor = EvaluationProcessor(self.project, self.registry)

    def evaluate(self):
        self.evaluation_processor.evaluate()
    
    def method_level_evaluate(self):
        self.evaluation_processor.method_level_evaluate()