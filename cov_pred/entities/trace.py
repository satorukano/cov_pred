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