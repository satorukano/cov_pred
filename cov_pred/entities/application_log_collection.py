class ApplicationLogCollection:

    def __init__(self, application_logs, module):
        self.application_logs = {}
        self.module = module
        self.set_application_logs(application_logs)

    def set_application_logs(self, application_logs):
        for log in application_logs:
            if "/test/" in log.file:
                continue

            if "/" + self.module + "/" in log.file:
                continue

            if log.thread_id not in self.application_logs:
                self.application_logs[log.thread_id] = []
            self.application_logs[log.thread_id].append(log)
        
        for thread_id, logs in self.application_logs.items():
            self.application_logs[thread_id] = sorted(self.remove_duplicate_logs(logs), key=lambda x: x.order)

    
    def remove_duplicate_logs(self, application_logs):

        seen_combinations = set()
        unique_logs = []
        
        for log in application_logs:

            combination_key = (log.line, log.class_name, log.thread_id)
            
            if combination_key not in seen_combinations:
                seen_combinations.add(combination_key)
                unique_logs.append(log)
        
        return unique_logs
