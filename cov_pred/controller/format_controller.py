from processor.format_processor import FormatProcessor
from processor.method_level_format_processor import MethodLevelFormatProcessor
from processor.bulk_format_processor import BulkFormatProcessor
from database import Database
from utils.java_util import extract_java_classes, extract_empty_and_comment_lines, extract_all_class_and_method_info
from utils.git import Git
from manager.trace_manager import TraceManager
from manager.application_log_manager import ApplicationLogManager
from processor.execution_path_processor import ExecutionPathProcessor
from utils.gpt import GPT

import os
import json

class FormatController:
    def __init__(self, project, registry):
        self.project = project
        self.registry = registry
        self.database = Database()

    def setup(self):
        git = Git(self.project, self.registry, "./repos", self.database)
        git.clone_or_checkout_commit()
        self.class_to_path = extract_java_classes(f"./repos/{self.project}")
        self.empty_and_comment_lines = extract_empty_and_comment_lines(f"./repos/{self.project}")
        self.trace_manager = TraceManager(self.database, self.registry, self.project)
        self.application_log_manager = ApplicationLogManager(self.database, self.registry, self.project, self.class_to_path)
        self.signatures_including_logs = self.application_log_manager.get_signatures_including_logs()
        self.execution_path_processor = ExecutionPathProcessor(self.trace_manager, self.application_log_manager)
        self.collection = self.execution_path_processor.link_logs_to_execution_path()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.gpt = GPT(OPENAI_API_KEY)
    
    def setup_line_level(self):
        self.format_processor = FormatProcessor(self.project, self.registry, self.signatures_including_logs, self.gpt, self.empty_and_comment_lines)

    def setup_method_level(self):
        self.format_processor = MethodLevelFormatProcessor(self.project, self.registry, self.signatures_including_logs, self.gpt, extract_all_class_and_method_info(f"./repos/{self.project}"), test_percentage=0.2, log_count_threshold=1)

    def setup_bulk_line_level(self):
        self.format_processor = BulkFormatProcessor(self.project, self.registry, self.signatures_including_logs, self.gpt, self.empty_and_comment_lines, self.application_log_manager, self.trace_manager, test_percentage=0.2, log_count_threshold=1)

    def format_for_training(self) -> dict:
        self.format_processor.format_for_training(self.collection)
    
    def format_for_validation(self, model):
        self.format_processor.format_for_validation(self.application_log_manager, model)
    
    def make_validation_oracle(self):
        self.format_processor.make_validation_oracle(self.trace_manager)