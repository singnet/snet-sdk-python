from grpc import RpcError


class SnetSDKError(Exception):
    """Base SNET SDK exception class"""

    pass


# ==================== Blockchain interaction Errors ====================


class ContractError(SnetSDKError):
    pass


class TransactionError(ContractError):
    pass


class TransactionTimeoutError(TransactionError):
    def __init__(self, tx_hash: str, timeout: int):
        super().__init__(f"Transaction {tx_hash} was not mined within {timeout} seconds!")


class TransactionRevertedError(TransactionError):
    def __init__(self, tx_hash: str):
        super().__init__(f"Transaction {tx_hash} failed and was reverted by the network!")


class EventNotFoundError(TransactionError):
    def __init__(self, tx_hash: str, event_name: str):
        super().__init__(
            f"Transaction {tx_hash} succeeded, but the expected event '{event_name}' was not emitted."
        )


class RegistryContractError(ContractError):
    pass


class OrganizationNotFoundError(RegistryContractError):
    def __init__(self, org_id: str):
        super().__init__(f"Organization with org_id={org_id} doesn't exist!")


class ServiceNotFoundError(RegistryContractError):
    def __init__(self, org_id: str, service_id: str):
        super().__init__(f"Service with org_id={org_id} service_id={service_id} doesn't exist!")


class UnauthorizedCallerError(TransactionError):
    pass


class UnauthorizedOrgMemberError(UnauthorizedCallerError):
    def __init__(self, org_id: str, address: str):
        super().__init__(f"Address {address} isn't owner or member of the organization {org_id}!")


# ==================== Metadata Errors ====================


class MetadataMismatchError(ValueError, SnetSDKError):
    pass


class ServiceMetadataMismatchError(MetadataMismatchError):
    pass


class OrganizationMetadataMismatchError(MetadataMismatchError):
    pass


# ==================== Storage Provider Errors ====================


class StorageProviderError(SnetSDKError):
    pass


class UnsupportedStorageTypeError(ValueError, StorageProviderError):
    def __init__(self, storage_type: str):
        super().__init__(f"Unsupported storage type: {storage_type}!")


class LighthouseError(StorageProviderError):
    def __init__(self):
        super().__init__(
            "Lighthouse internal error! Most likely, you did not specify LIGHTHOUSE_TOKEN in the config or it expired."
        )


class PublishProtoError(ValueError, StorageProviderError):
    pass


class WrongDirectoryError(PublishProtoError):
    def __init__(self, dir_path: str):
        super().__init__(f"{dir_path} isn't a directory or it doesn't exist!")


class ProtoFilesNotFoundError(PublishProtoError):
    def __init__(self, dir_path: str):
        super().__init__(f"Cannot find any .proto file in {dir_path}!")


# ==================== Training Errors ====================


class TrainingError(SnetSDKError):
    pass


class WrongDatasetError(TrainingError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        exception_msg = "Dataset check failed:\n"
        for check in errors:
            exception_msg += f"\t{check}\n"
        super().__init__(exception_msg)


class WrongMethodError(ValueError, TrainingError):
    def __init__(self, method_name: str):
        super().__init__(f"Method with name {method_name} not found!")


class NoTrainingError(ValueError, TrainingError):
    def __init__(self, org_id: str, service_id: str):
        super().__init__(
            f"Training is not implemented for the service with org_id={org_id} and service_id={service_id}!"
        )


class GRPCError(RpcError, TrainingError):
    def __init__(self, error: RpcError):
        super().__init__(f"An error occurred during the grpc call: {error}.")


class NoSuchModelError(ValueError, TrainingError):
    def __init__(self, model_id: str):
        super().__init__(f"Model with id {model_id} not found!")


# ==================== Service Client Errors ====================


class ServiceClientError(SnetSDKError):
    pass


class NoGroupsFoundError(ServiceClientError):
    def __init__(self, org_id: str, service_id: str):
        super().__init__(f"Service with org_id={org_id} service_id={service_id} has no groups!")


class GroupNotFoundError(ServiceClientError):
    def __init__(self, org_id: str, service_id: str, group_name: str):
        super().__init__(
            f"Service with org_id={org_id} service_id={service_id} has no group with group_name={group_name}!"
        )
