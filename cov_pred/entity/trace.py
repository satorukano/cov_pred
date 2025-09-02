class Trace:

    def __init__(self, path: str, thread_num: int, order: int):
        self.path = path
        self.file = None
        self.file = self.get_file()
        self.line = None
        self.line = self.get_line()
        self.thread_num = "thread_" + str(thread_num)
        self.order = order

    def get_line(self) -> str | None:
        if self.line is not None:
            return self.line
        return self.path.split('@')[-1]

    def get_file(self) -> str | None:
        if self.file is not None:
            return self.file
        return self.path.split(";")[0]
    
    def equals(self, other: 'Trace') -> bool:
        return self.path == other.path and self.thread_num == other.thread_num and self.order == other.order
    
    def __str__(self):
        return f"Trace(path={self.path}, thread_num={self.thread_num}, order={self.order})"