from processor.format_processor import FormatProcessor
from processor.method_level_format_processor import MethodLevelFormatProcessor
from database import Database
from utils.java_util import extract_java_classes, extract_empty_and_comment_lines, extract_all_class_and_method_info
from utils.git import clone_or_checkout_commit
from manager.trace_manager import TraceManager
from manager.application_log_manager import ApplicationLogManager
from processor.execution_path_processor import ExecutionPathProcessor
from utils.gpt import GPT

import os
import json

class FormatController:
    def __init__(self, project, registry, module):
        self.project = project
        self.registry = registry
        self.module = module
        self.database = Database()

    def setup(self):
        self.class_to_path = extract_java_classes(f"./repos/{self.project}")
        self.empty_and_comment_lines = extract_empty_and_comment_lines(f"./repos/{self.project}")
        with open("settings/repo_info.json") as f:
            repo_info = json.load(f)
        commit_hash = self.database.get_commit_hash(self.registry)
        clone_or_checkout_commit(repo_info[self.project]['url'], "./repos", commit_hash)
        self.trace_manager = TraceManager(self.database, self.registry, self.project, self.module)
        self.application_log_manager = ApplicationLogManager(self.database, self.registry, self.project, self.class_to_path, self.module)
        self.signatures_including_logs = self.application_log_manager.get_signatures_including_logs()
        self.execution_path_processor = ExecutionPathProcessor(self.trace_manager, self.application_log_manager)
        self.collection = self.execution_path_processor.link_logs_to_execution_path()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.gpt = GPT(OPENAI_API_KEY)
    
    def setup_line_level(self):
        self.format_processor = FormatProcessor(self.signatures_including_logs, self.gpt, self.empty_and_comment_lines)

    def setup_method_level(self):
        self.format_processor = MethodLevelFormatProcessor(self.signatures_including_logs, self.gpt, extract_all_class_and_method_info(f"./repos/{self.project}"), test_percentage=0.2, log_count_threshold=1)

    def format_for_training(self) -> dict:
        self.format_processor.format_for_training(self.collection, self.project, self.registry)
    
    def format_for_validation(self, model):
        self.format_processor.format_for_validation(self.application_log_manager, self.project, self.registry, model)
    
    def make_validation_oracle(self):
        self.format_processor.make_validation_oracle(self.trace_manager, self.project, self.registry)

    def method_level_format(self):
        self.format_processor.method_level_format(self.collection, self.project, self.registry)