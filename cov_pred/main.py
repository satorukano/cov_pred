from controller.trace_controller import TraceController
from controller.application_log_controller import ApplicationLogController
from processor.execution_path_processor import ExecutionPathProcessor
from database import Database
from utils.git import clone_or_checkout_commit
from utils.java_util import extract_java_classes
import sys
import json

def main(project, module, registry):
    db = Database()
    with open("settings/repo_info.json") as f:
        repo_info = json.load(f)
    commit_hash = db.get_commit_hash(registry)
    clone_or_checkout_commit(repo_info[project]['url'], "./repos", commit_hash)
    class_to_path = extract_java_classes(f"./repos/{project}")
    trace_controller = TraceController(db, registry, project, module)
    application_log_controller = ApplicationLogController(db, registry, project, class_to_path, module)
    execution_path_processor = ExecutionPathProcessor(trace_controller, application_log_controller)
    collection = execution_path_processor.link_logs_to_execution_path()
    print(collection)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main.py <project> <module> <registry>")
        sys.exit(1)
    
    project = sys.argv[1]
    module = sys.argv[2]
    registry = sys.argv[3]
    
    main(project, module, registry)