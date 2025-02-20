from grpc import RpcError


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


class NoTrainingException(Exception):
    def __init__(self, org_id: str, service_id: str):
        super().__init__(f"Training is not implemented for the service with org_id={org_id} and service_id={service_id}!")


class GRPCException(RpcError):
    def __init__(self, error: RpcError):
        super().__init__(f"An error occurred during the grpc call: {error}.")


class NoSuchModelException(Exception):
    def __init__(self, model_id: str):
        super().__init__(f"Model with id {model_id} not found!")

