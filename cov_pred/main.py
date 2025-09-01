from controller.trace_controller import TraceController
from controller.application_log_controller import ApplicationLogController
from processor.execution_path_processor import ExecutionPathProcessor
from processor.format_processor import FormatProcessor
from database import Database
from utils.git import clone_or_checkout_commit
from utils.java_util import extract_java_classes
from utils.gpt import GPT
import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()

def main(project, module, registry):
    db = Database()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    with open("settings/repo_info.json") as f:
        repo_info = json.load(f)
    commit_hash = db.get_commit_hash(registry)
    clone_or_checkout_commit(repo_info[project]['url'], "./repos", commit_hash)
    class_to_path = extract_java_classes(f"./repos/{project}")
    trace_controller = TraceController(db, registry, project, module)
    application_log_controller = ApplicationLogController(db, registry, project, class_to_path, module)
    signatures_including_logs = application_log_controller.get_signatures_including_logs()
    execution_path_processor = ExecutionPathProcessor(trace_controller, application_log_controller)
    collection = execution_path_processor.link_logs_to_execution_path()
    gpt = GPT(OPENAI_API_KEY)
    formatter = FormatProcessor(signatures_including_logs, gpt)
    formatter.format_for_training(collection, project, registry)
    formatter.format_for_validation(application_log_controller, project, registry)
    formatter.make_validation_oracle(trace_controller, project, registry)
    gpt.finetune(project, registry, "gpt-4.1-nano-2025-04-14")



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main.py <project> <module> <registry>")
        sys.exit(1)
    
    project = sys.argv[1]
    module = sys.argv[2]
    registry = sys.argv[3]
    
    main(project, module, registry)