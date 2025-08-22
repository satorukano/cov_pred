import re
from utils.java_util import extract_java_classes

class ApplicationLog:

    def __init__(self, log_statement, project, order, class_to_path):
        self.log_statement = log_statement
        self.project = project
        self.class_to_path = class_to_path
        self.thread_id = self.get_thread_id()
        self.line = self.get_line()
        self.class_name = self.get_class()
        self.order = order
        self.patterns = {
            "zookeeper" : {
                "thread_id": r'[A-Za-z_$]+(?=:[A-Za-z_$]+@\d+])',
                "line": r'[A-Za-z_$]+@\d+',
                "class": r'[A-Za-z_$]+@\d+'
            }
        }
        self.file = self.set_file()

    
    def get_thread_id(self):

        if self.thread_id is not None:
            return self.thread_id

        pattern = self.patterns[self.project]["thread_id"]
        match = re.search(pattern, self.log_statement)
        if match:
            return match.group(0)
        return None

    def get_line(self):
        if self.line is not None:
            return self.line

        pattern = self.patterns[self.project]["line"]
        match = re.search(pattern, self.log_statement)
        if match:
            return match.group(0).split('@')[-1]
        return None

    def get_class(self):
        if self.class_name is not None:
            return self.class_name

        pattern = self.patterns[self.project]["class"]
        match = re.search(pattern, self.log_statement)
        if match:
            class_name = match.group(0).split('@')[0]
            if "$" in class_name:
                return class_name.split("$")[-1]
            return class_name
        return None

    def set_file(self):
        file = self.class_to_path.get(self.class_name)
        return file
    
    def get_file(self):
        return self.file
