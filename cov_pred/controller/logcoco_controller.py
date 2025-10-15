from processor.logcoco_processor import LogcocoProcessor
from database import Database

class LogcocoController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        database = Database()
        self.logcoco_processor = LogcocoProcessor(self.project, self.registry, database)

    def prepare_log_data(self):
        self.logcoco_processor.prepare_log_data()