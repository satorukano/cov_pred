from utils.git import Git
from database import Database
from utils.logcoco_util import get_validation_signatures

import os

class LogcocoProcessor:
    def __init__(self, project: str, registry: str, database: Database):
        self.project = project
        self.registry = registry
        self.git = Git(project, registry, "./repos", database)
        self.git.clone_or_checkout_commit()
        self.database = database

    def prepare_log_data(self):
        logs = self.database.get_logs(self.registry)
        logs_with_signature = {}
        for log in logs:
            signature = log['signature']
            if signature not in logs_with_signature:
                logs_with_signature[signature] = []
            logs_with_signature[signature].append(log)
        validation_signatures = get_validation_signatures(self.git.project, self.git.registry)
        for signature in validation_signatures:
            signature_logs = logs_with_signature.get(signature, [])
            signature_logs.sort(key=lambda x: x['invoked_order'])
            method_name = signature.split(';')[-1]
            if signature_logs:
                os.makedirs(f"LogCoCo/{self.project}_{self.registry}/{method_name}", exist_ok=True)
            with open(f"LogCoCo/{self.project}_{self.registry}/{method_name}/log.txt", 'w') as f:
                for log in signature_logs:
                    f.write(log['statement'] + '\n')    