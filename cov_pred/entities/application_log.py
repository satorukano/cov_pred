import re
from utils.java_util import extract_java_classes

class ApplicationLog:

    def __init__(self, log_statement: str, project: str, order: int, class_to_path: dict[str, str]):
        self.patterns = {
            "zookeeper" : {
                "line": r'[A-Za-z_$]+@\d+',
                "class": r'[A-Za-z0-9_$]+@\d+'
            }
        }
        self.log_statement = log_statement
        self.project = project
        self.class_to_path = class_to_path
        self.thread_id = None
        self.thread_id = self.get_thread_id()
        self.line = None
        self.line = self.get_line()
        self.class_name = None
        self.class_name = self.get_class()
        self.order = order
        self.file = self.set_file()


    def get_log_statement(self) -> str:
        return self.log_statement


    def get_thread_id(self) -> str | None:
        if self.thread_id is not None:
            return self.thread_id
        log_levels = ['INFO', 'DEBUG', 'WARN', 'ERROR']
        for level in log_levels:
            level_index = self.log_statement.find(level)
            if level_index == -1:
                continue
            after_level = self.log_statement[level_index + len(level):]
            bracket_start = after_level.find('[')
            if bracket_start == -1:
                return None
            # just in case bracket in bracket
            bracket_content_end = after_level.find('@', bracket_start)

            if bracket_content_end == -1:
                return None
            bracket_content = after_level[bracket_start + 1:bracket_content_end]
            thread_id = "".join(bracket_content.split(':')[:-1])
            return thread_id
        return None

    def get_line(self) -> str | None:
        if self.line is not None:
            return self.line

        pattern = self.patterns[self.project]["line"]
        match = re.search(pattern, self.log_statement)
        if match:
            return match.group(0).split('@')[-1]
        return None

    def get_class(self) -> str | None:
        if self.class_name is not None:
            return self.class_name

        pattern = self.patterns[self.project]["class"]
        match = re.search(pattern, self.log_statement)
        if match:
            class_name = match.group(0).split('@')[0]
            if "$" in class_name:
                return class_name.replace("$", ".")
            return class_name
        return None

    def set_file(self):
        file = self.class_to_path.get(self.class_name)
        return file

    def get_file(self) -> str | None:
        return self.file
