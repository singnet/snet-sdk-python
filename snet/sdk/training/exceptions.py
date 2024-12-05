
class WrongDatasetException(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        exception_msg = "Dataset check failed:\n"
        for check in errors:
            exception_msg += f"\t{check}\n"
        super().__init__(exception_msg)

class WrongMethodException(Exception):
    def __init__(self, method_name: str):
        super().__init__(f"Method with name {method_name} not found!")







