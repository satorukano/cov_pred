class Trace:

    def __init__(self, path, thread_num, order):
        self.path = path
        self.file = self.get_file()
        self.line = self.get_line()
        self.thread_num = "thread_" + str(thread_num)
        self.order = order

    def get_line(self):
        if self.line is not None:
            return self.line
        return self.path.split('@')[-1]
    
    def get_file(self):
        if self.file is not None:
            return self.file
        return self.path.split(";")[0]