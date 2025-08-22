class ExecutionPathProcessor:
    def __init__(self, execution_path_controller, log_controller):
        self.execution_path_controller = execution_path_controller
        self.log_controller = log_controller
    
    def link_logs_to_execution_path(self):
        thread_num_to_thread_id = self.check_link_logs_to_execution_path()
        application_logs = self.log_controller.get_logs()
        execution_paths = self.execution_path_controller.get_execution_paths()
        collection = {}
        for signature in application_logs.keys():
            collection[signature] = {}
            for thread_num, logs in application_logs[signature].items():
                if thread_num not in thread_num_to_thread_id:
                    break
                thread_id = thread_num_to_thread_id[thread_num]
                execution_path = execution_paths.get(signature)
                execution_path = execution_path.execution_path.get(thread_id, [])
                log_count = 0
                collection[signature][thread_num] = []
                previous_position = 0
                previous_log = ""
                while log_count < len(logs):
                    log = logs[log_count]
                    found = self.find_log_execution(log, execution_path)
                    log_count += 1
                    if found is None:
                        continue
                    executed_between_logs = execution_path[previous_position:found+1]
                    collection[signature][thread_num].append({(previous_log, log): executed_between_logs})
                    previous_position = found + 1
                    previous_log = log
                    execution_path = execution_path[:found+1]
                    log_count += 1


    def check_link_logs_to_execution_path(self):
        execution_paths = self.execution_path_controller.get_execution_paths()
        application_logs = self.log_controller.get_logs()
        thread_num_to_thread_id = {}

        for signature, application_logs in application_logs.items():
            execution_path = execution_paths.get(signature)
            for thread, application_log in application_logs:
                for thread_num, execution_path in execution_paths.items():
                    found = self.check_thread(application_log, execution_path)
                    if found:
                        thread_num_to_thread_id[thread_num] = thread
                        break
        return thread_num_to_thread_id

    def check_thread(self, application_log, execution_path):
        for log in application_log:
            found = self.find_log_execution(log, execution_path)
            if found is not None:
                execution_path = execution_path[:found+1]
                continue
            return False
        return True

    def find_log_execution(self, application_log, execution_path):
        index = 0
        for trace in execution_path.traces:
            if application_log.get_file() == trace.get_file() and application_log.get_line() == trace.get_line():
                return index
            index += 1
        return None

