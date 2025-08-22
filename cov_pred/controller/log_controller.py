from entities.application_log import ApplicationLog
from entities.application_log_collection import ApplicationLogCollection

class LogController:

    def __init__(self, database, registry, project):
        self.db = database
        self.registry = registry
        self.project = project
        self.application_logs = self.get_logs()

    
    def get_logs(self):
        if self.application_logs:
            return self.application_logs

        application_logs = self.db.get_logs(self.registry)
        application_logs_with_signature = {}
        for log in application_logs:
            application_log = ApplicationLog(log['statement'], self.project, log['invoked_order'])
            if log['signature'] not in application_logs_with_signature:
                application_logs_with_signature[log['signature']] = []
            application_logs_with_signature[log['signature']].append(application_log)

        application_log_collection_with_signature = {}

        for signature, logs in application_logs_with_signature.items():
            application_log_collection_with_signature[signature] = ApplicationLogCollection(logs)

        return application_log_collection_with_signature
