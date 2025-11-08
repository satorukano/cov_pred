from entity.trace import Trace
from database import Database

class TraceManager:

    def __init__(self, database: Database, registry: str, project: str):
        self.db = database
        self.registry = registry
        self.project = project
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

        # Remove duplicated threads
        execution_path_for_check = execution_path.copy()
        for thread_num, traces in execution_path_for_check.items():
            for thread_num2, traces2 in execution_path_for_check.items():
                if thread_num != thread_num2:
                    if self.check_equal(traces, traces2) and thread_num2 in execution_path:
                        execution_path.pop(thread_num2)
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
    
    def check_equal(self, execution_path1: list[Trace], execution_path2: list[Trace]) -> bool:
        if len(execution_path1) != len(execution_path2):
            return False
        
        for i in range(len(execution_path1)):
            if execution_path1[i].equals(execution_path2[i]) is False:
                return False
        return True