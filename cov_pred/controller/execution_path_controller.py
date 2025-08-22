from entities.execution_path import ExecutionPath
from entities.trace import Trace

class ExecutionPathController:

    def __init__(self, database, registry, project, module):
        self.db = database
        self.registry = registry
        self.project = project
        self.module = module
        self.signatures = self.db.get_signatures(self.registry)
        self.execution_paths = self.get_execution_paths()

    def get_execution_paths(self):
        if self.execution_paths:
            return self.execution_paths

        execution_paths_with_signatures = {}
        for signature in self.signatures:
            paths = self.db.get_execution_path(self.registry, signature)
            order = 1
            traces = []
            for path in paths:
                if "/test/" in path["path"]:
                    continue

                if "/" + self.module + "/" not in path["path"]:
                    continue
                
                trace = Trace(path['path'], path['thread_num'], order)
                traces.append(trace)
                order += 1
            execution_path = ExecutionPath(traces)
            execution_paths_with_signatures[signature] = execution_path
        return execution_paths_with_signatures
    
    def get_signatures(self):
        return self.signatures
