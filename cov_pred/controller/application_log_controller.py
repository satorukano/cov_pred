from entities.application_log import ApplicationLog
from database import Database

class ApplicationLogController:

    def __init__(self, database: Database, registry: str, project: str, class_to_path: dict[str, str], module: str):
        self.db = database
        self.registry = registry
        self.project = project
        self.class_to_path = class_to_path
        self.module = module
        self.application_logs = None
        self.application_logs = self.get_logs()


    def get_logs(self) -> dict[str, dict[str, list[ApplicationLog]]]:
        if self.application_logs:
            return self.application_logs

        application_logs = self.db.get_logs(self.registry)
        application_logs_with_signature = {}
        for log in application_logs:
            application_log = ApplicationLog(log['statement'], self.project, log['invoked_order'], self.class_to_path)
            if application_log.get_file() is None:
                continue
            if "/test/" in application_log.get_file() or self.module + "/" not in application_log.get_file():
                continue
            if log['signature'] not in application_logs_with_signature:
                application_logs_with_signature[log['signature']] = []
            application_logs_with_signature[log['signature']].append(application_log)
        
        for signature, logs in application_logs_with_signature.items():
            application_logs_with_signature[signature] = self.classify_logs_by_thread(logs)
        return application_logs_with_signature
    
    def classify_logs_by_thread(self, logs: list[ApplicationLog]) -> dict[str, list[ApplicationLog]]:
        application_logs = {}
        for log in logs:
            if log.get_thread_id() not in application_logs:
                application_logs[log.get_thread_id()] = []
            application_logs[log.get_thread_id()].append(log)

        for thread_num, logs in application_logs.items():
            application_logs[thread_num] = sorted(self.remove_duplicated_logs(logs), key=lambda x: x.order)
        return application_logs
    
    def remove_duplicated_logs(self, logs: dict[str, ApplicationLog]) -> list[ApplicationLog]:
        seen_combinations = set()
        unique_logs = []

        for log in logs:

            combination_key = (log.line, log.class_name, log.thread_id)
            
            if combination_key not in seen_combinations:
                seen_combinations.add(combination_key)
                unique_logs.append(log)
        
        return unique_logs
    
    def get_logs_by_signature(self, signature: str) -> dict[str, list[ApplicationLog]]:
        if signature in self.application_logs:
            return self.application_logs[signature]
        return {}
    
    def get_logs_by_thread(self, signature: str, thread_id: str) -> list[ApplicationLog]:
        logs_by_signature = self.get_logs_by_signature(signature)
        if logs_by_signature and thread_id in logs_by_signature:
            return logs_by_signature[thread_id]
        return []