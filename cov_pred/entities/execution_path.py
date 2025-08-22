class ExecutionPath:

    def __init__(self, traces):
        self.execution_path = {}
        self.set_execution_path(traces)

    def set_execution_path(self, traces):
        for trace in traces:
            if "/test/" in trace.path:
                continue

            if trace.thread_num not in self.execution_path:
                self.execution_path[trace.thread_num] = []
            self.execution_path[trace.thread_num].append(trace)
        
        for thread_num, traces in self.execution_path.items():
            self.execution_path[thread_num] = sorted(traces, key=lambda x: x.order)
        
