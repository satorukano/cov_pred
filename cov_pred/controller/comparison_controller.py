from processor.comparison_processor import ComparisonProcessor
from database import Database

class ComparisonController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        database = Database()
        self.comparison_processor = ComparisonProcessor(self.project, self.registry, database)

    def prepare_log_data_for_logcoco(self):
        self.comparison_processor.prepare_log_data_for_logcoco()