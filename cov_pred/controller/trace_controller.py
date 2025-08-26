from entities.trace import Trace
from database import Database

class TraceController:

    def __init__(self, database: Database, registry: str, project: str, module: str):
        self.db = database
        self.registry = registry
        self.project = project
        self.module = module
        self.signatures = self.db.get_signatures(self.registry)
        self.execution_paths = None
        self.execution_paths = self.get_execution_paths()

    def get_execution_paths(self) -> dict[str, dict[str, list[Trace]]]:
        if self.execution_paths:
            return self.execution_paths

        execution_paths = {}
        for signature in self.signatures:
            paths = self.db.get_execution_path(self.registry, signature)
            order = 1
            traces = []
            for path in paths:
                if "/test/" in path["path"]:
                    continue

                if self.module + "/" not in path["path"]:
                    continue

                trace = Trace(path['path'], path['thread_id'], order)
                traces.append(trace)
                order += 1
            execution_path = self.classify_traces_by_thread(traces)
            execution_paths[signature] = execution_path
        return execution_paths

    def get_signatures(self):
        return self.signatures
    
    def classify_traces_by_thread(self, traces: list[Trace]) -> dict[str, list[Trace]]:
        execution_path = {}
        for trace in traces:
            if trace.thread_num not in execution_path:
                execution_path[trace.thread_num] = []
            execution_path[trace.thread_num].append(trace)
        
        for thread_num, traces in execution_path.items():
            execution_path[thread_num] = sorted(traces, key=lambda x: x.order)
        return execution_path
    
    def get_traces_by_signature(self, signature: str) -> dict[str, list[Trace]]:
        if signature in self.execution_paths:
            return self.execution_paths[signature]
        return {}

    def get_traces_by_thread(self, signature: str, thread_num: str) -> list[Trace]:
        traces_by_signature = self.get_traces_by_signature(signature)
        if traces_by_signature and thread_num in traces_by_signature:
            return traces_by_signature[thread_num]
        return {}
    
    def get_threads_by_signature(self, signature: str) -> list[str]:
        traces_by_signature = self.get_traces_by_signature(signature)
        if traces_by_signature:
            return list(traces_by_signature.keys())
        return []
    
    def print_execution_path(self, signature: str):
        traces_by_signature = self.get_traces_by_signature(signature)
        if not traces_by_signature:
            print(f"No execution path found for signature: {signature}")
            return
        
        for thread_num, traces in traces_by_signature.items():
            print(f"Thread: {thread_num}")
            for trace in traces:
                print(f"  {trace.path}")
            print("\n")