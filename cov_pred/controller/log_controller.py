from entities.application_log import ApplicationLog
from entities.application_log_collection import ApplicationLogCollection

class LogController:

    def __init__(self, database, registry, project, class_to_path, module):
        self.db = database
        self.registry = registry
        self.project = project
        self.class_to_path = class_to_path
        self.module = module
        self.application_logs = self.get_logs()

    
    def get_logs(self):
        if self.application_logs:
            return self.application_logs

        application_logs = self.db.get_logs(self.registry)
        application_logs_with_signature = {}
        for log in application_logs:
            application_log = ApplicationLog(log['statement'], self.project, log['invoked_order'], self.class_to_path)
            if log['signature'] not in application_logs_with_signature:
                application_logs_with_signature[log['signature']] = []
            application_logs_with_signature[log['signature']].append(application_log)

        application_log_collection_with_signature = {}

        for signature, logs in application_logs_with_signature.items():
            application_log_collection_with_signature[signature] = ApplicationLogCollection(logs, self.module)

        return application_log_collection_with_signature
