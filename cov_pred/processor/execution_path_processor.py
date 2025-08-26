from controller.trace_controller import TraceController
from controller.application_log_controller import ApplicationLogController

class ExecutionPathProcessor:
    def __init__(self, trace_controller: TraceController, application_log_controller: ApplicationLogController):
        self.trace_controller = trace_controller
        self.application_log_controller = application_log_controller

    def link_logs_to_execution_path(self):
        thread_id_to_thread_num = self.check_link_logs_to_execution_path()
        collection = {}
        for signature in self.trace_controller.get_signatures():
            collection[signature] = {}
            for thread_id, logs in self.application_log_controller.get_logs_by_signature(signature).items():
                if thread_id not in thread_id_to_thread_num[signature]:
                    break
                thread_num = thread_id_to_thread_num[signature][thread_id]
                execution_path = self.trace_controller.get_traces_by_thread(signature, thread_num)
                log_count = 0
                collection[signature][thread_id] = []
                previous_position = 0
                previous_log = ""
                while log_count < len(logs):
                    log = logs[log_count]
                    found = self.find_log_execution(log, execution_path)
                    log_count += 1
                    if found is None:
                        continue
                    executed_between_logs = execution_path[previous_position:found+1]
                    collection[signature][thread_id].append({(previous_log, log): executed_between_logs})
                    previous_position = found + 1
                    previous_log = log
                    execution_path = execution_path[found+1:]
        return collection


    def check_link_logs_to_execution_path(self) -> dict[str, str]:
        signatures = self.trace_controller.get_signatures()
        thread_id_to_thread_num = {}
        for signature in signatures:
            for thread_id, logs in self.application_log_controller.get_logs_by_signature(signature).items():
                for thread_num, execution_path in self.trace_controller.get_traces_by_signature(signature).items():
                    if execution_path is None:
                        continue
                    if self.check_thread(logs, execution_path):
                        if signature not in thread_id_to_thread_num:
                            thread_id_to_thread_num[signature] = {}
                        thread_id_to_thread_num[signature][thread_id] = thread_num
                    elif thread_id == "main" and thread_num == "thread_0":
                        print(f"Warning: main thread not matched for signature {signature}")
        return thread_id_to_thread_num

    def check_thread(self, application_log, execution_path) -> bool:
        for log in application_log:
            found = self.find_log_execution(log, execution_path)
            if found is not None:
                execution_path = execution_path[found+1:]
                continue
            return False
        return True

    def find_log_execution(self, application_log, execution_path) -> int | None:
        index = 0
        for trace in execution_path:
            if application_log.get_file() == trace.get_file() and application_log.get_line() == trace.get_line():
                return index
            index += 1
        return None

