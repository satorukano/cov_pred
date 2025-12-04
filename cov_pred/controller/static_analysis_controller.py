from processor.static_analysis_processor import StaticAnalysisProcessor
from processor.execution_path_processor import ExecutionPathProcessor
from manager.trace_manager import TraceManager
from manager.application_log_manager import ApplicationLogManager
from database import Database
from utils.java_util import extract_java_classes, extract_all_class_and_method_info
from utils.git import Git

class StaticAnalysisController:
    def __init__(self, project: str, registry: str):
        self.project = project
        self.registry = registry
        self.database = Database()
        git = Git(self.project, self.registry, "./repos", self.database)
        git.clone_or_checkout_commit()
        self.class_to_path = extract_java_classes(f"./repos/{self.project}")
        self.trace_manager = TraceManager(self.database, self.registry, self.project)
        self.application_log_manager = ApplicationLogManager(self.database, self.registry, self.project, self.class_to_path)
        self.signatures_including_logs = self.application_log_manager.get_signatures_including_logs()
        self.execution_path_processor = ExecutionPathProcessor(self.trace_manager, self.application_log_manager)
        self.collection = self.execution_path_processor.link_logs_to_execution_path()
        self.static_analysis_processor = StaticAnalysisProcessor(self.project, self.registry, extract_all_class_and_method_info(f"./repos/{self.project}"))

    def analyze(self):
        self.static_analysis_processor.analyze(self.collection, self.signatures_including_logs, self.trace_manager)
    
    def identify_log_containing_methods_line(self):
        self.static_analysis_processor.identify_log_containing_methods_line(self.application_log_manager)
    
    def identify_log_containing_methods(self):
        self.static_analysis_processor.identify_log_containing_methods(self.application_log_manager)
