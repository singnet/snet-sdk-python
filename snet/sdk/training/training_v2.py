import enum
from pathlib import PurePath, Path
import os
from zipfile import ZipFile

import grpc

from snet.sdk import generic_client_interceptor
from snet.sdk.payment_strategies.dynamic_price_payment_strategy import DynamicPricePaymentStrategy
from snet.sdk.service_client import ServiceClient, _ClientCallDetails

from snet.sdk.resources.proto import training_daemon_pb2 as training_daemon
from snet.sdk.resources.proto import training_daemon_pb2_grpc as training_daemon_grpc
from snet.sdk.resources.proto import training_v2_pb2 as training


class ModelMethodMessage(enum.Enum):
    CreateModel = "__CreateModel"
    ValidateModelPrice = "__ValidateModelPrice"
    TrainModelPrice = "__TrainModelPrice"
    DeleteModel = "__DeleteModel"
    GetTrainingMetadata = "__GetTrainingMetadata"
    GetAllModels = "__GetAllModels"
    GetModel = "__GetModel"
    UpdateModel = "__UpdateModel"
    GetDatasetRequirements = "__GetDatasetRequirements"
    UploadAndValidate = "__UploadAndValidate"
    ValidateModel = "__ValidateModel"
    TrainModel = "__TrainModel"


class ModelStatus(enum.Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    TRAINING = "TRAINING"
    READY_TO_USE = "READY_TO_USE"
    ERRORED = "ERRORED"
    DELETED = "DELETED"


class TrainingV2:
    def __init__(self, service_client: ServiceClient):
        self.service_client = service_client
        self.is_enabled = self._check_training()
        self.payment_strategy = DynamicPricePaymentStrategy()

    """FREE METHODS TO CALL"""

    def create_model(self, method_name: str,
                     model_name: str,
                     model_description: str="",
                     is_public_accessible: bool=False,
                     addresses_with_access: list[str]=None):
        if addresses_with_access is None:
            addresses_with_access = []

        service_name, method_name = self._check_method_name(method_name)
        new_model = training.NewModel(name=model_name,
                                      description=model_description,
                                      grpc_method_name=method_name,
                                      grpc_service_name=service_name,
                                      is_public=is_public_accessible,
                                      address_list=addresses_with_access,
                                      organization_id=self.service_client.org_id,
                                      service_id=self.service_client.service_id,
                                      group_id=self.service_client.group["group_id"])
        auth_details = self._get_auth_details(ModelMethodMessage.CreateModel)
        create_model_request = training_daemon.NewModelRequest(authorization=auth_details,
                                                               model=new_model)
        response = self._call_method("create_model",
                                     request_data=create_model_request)
        return response

    def validate_model_price(self, model_id: str):
        auth_details = self._get_auth_details(ModelMethodMessage.ValidateModelPrice)
        validate_model_price_request = training_daemon.ValidateRequest(
            authorization=auth_details,
            model_id=model_id,
            training_data_link=""
        )
        response = self._call_method("validate_model_price",
                                     request_data=validate_model_price_request)
        return response

    def train_model_price(self, model_id: str):
        auth_details = self._get_auth_details(ModelMethodMessage.TrainModelPrice)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("train_model_price",
                                     request_data=common_request)
        return response

    def delete_model(self, model_id: str):
        auth_details = self._get_auth_details(ModelMethodMessage.DeleteModel)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("delete_model",
                                     request_data=common_request)
        return response

    def get_training_metadata(self):
        response = self._call_method("get_training_metadata")
        return response

    def get_all_models(self, status: ModelStatus=None,
                       is_public: bool=False,
                       model_name: str=""):
        if status:
            status = getattr(training.Status, status.value)
        auth_details = self._get_auth_details(ModelMethodMessage.GetAllModels)
        all_models_request = training_daemon.AllModelsRequest(
            authorization=auth_details,
            status=status,
            is_public=is_public,
            model_name=model_name,
            page_size=0,
            page=0
        )
        response = self._call_method("get_all_models",
                                     request_data=all_models_request)
        return response

    def get_model(self, model_id: str):
        auth_details = self._get_auth_details(ModelMethodMessage.GetModel)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("get_model",
                                     request_data=common_request)
        return response

    def update_model(self, model_id: str,
                     model_name: str="",
                     description: str="",
                     addresses_with_access: list[str]=None):
        if addresses_with_access is None:
            addresses_with_access = []
        auth_details = self._get_auth_details(ModelMethodMessage.UpdateModel)
        update_model_request = training_daemon.UpdateModelRequest(
            authorization=auth_details,model_id=model_id,
            model_name=model_name,
            description=description,
            address_list=addresses_with_access
        )
        response = self._call_method("update_model",
                                     request_data=update_model_request)
        return response

    def get_dataset_requirements(self, method_name: str, model_id: str=""):

        if model_id:
            requirements_request = training_daemon.DatasetRequirementsRequest(
                grpc_method_name="",
                grpc_service_name="",
                model_id=model_id
            )
        else:
            service_name, method_name = self._check_method_name(method_name)
            requirements_request = training_daemon.DatasetRequirementsRequest(
                grpc_method_name=method_name,
                grpc_service_name=service_name,
                model_id=""
            )
        response = self._call_method("get_dataset_requirements",
                                     request_data=requirements_request)
        return response

    """PAID METHODS TO CALL"""

    def upload_and_validate(self, model_id: str, zip_path: str | Path | PurePath, price: int):
        f = open(zip_path, 'rb')

        self._check_dataset(model_id, zip_path)

        auth_details = self._get_auth_details(ModelMethodMessage.UploadAndValidate)

        def request_iter(file):
            batch = file.read(1024*1024)
            while batch:
                yield training_daemon.UploadAndValidateRequest(
                    authorization=auth_details,
                    model_id=model_id,
                    data=batch
                )
                batch = file.read(1024*1024)

        response = self._call_method("upload_and_validate",
                                     request_data=request_iter(f),
                                     paid=True)
        f.close()
        return response

    def train_model(self, model_id: int, price: int):
        auth_details = self._get_auth_details(ModelMethodMessage.TrainModel)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("train_model",
                                     request_data=common_request,
                                     paid=True)
        return response

    """PRIVATE METHODS"""

    def _call_method(self, method_name: str,
                     request_data=None,
                     paid=False):
        try:
            stub = self._get_training_stub(paid=paid)
            if request_data is None:
                response = getattr(stub, method_name)()
            else:
                response = getattr(stub, method_name)(request_data)
            return response
        except Exception as e:
            # print("Exception: ", e)
            # TODO: parse exception
            raise e

    def _get_training_stub(self, paid=False):
        grpc_channel = self.service_client.get_grpc_base_channel()
        if paid:
            grpc_channel = self._get_grpc_channel(grpc_channel)
        return training_daemon_grpc.DaemonStub(grpc_channel)

    def _get_auth_details(self, method_msg: ModelMethodMessage):
        current_block_number = self.service_client.get_current_block_number()
        address = self.service_client.account.address
        signature = self.service_client.generate_training_signature(method_msg.value,
                                                                    address,
                                                                    current_block_number)
        auth_details = training_daemon.AuthorizationDetails(
            signature=bytes(signature),
            current_block=current_block_number,
            signer_address=address,
            message=method_msg.value
        )
        return auth_details

    def _check_method_name(self, method_name: str) -> tuple[str, str]:
        services_methods, _ = self.service_client.get_services_and_messages_info()
        for service, methods in services_methods.items():
            for method in methods:
                if method[0] == method_name:
                    return service, method[0]
        raise Exception(f"Method {method_name} not found!")

    def _check_training(self) -> bool:
        metadata_response = self.get_training_metadata()
        if len(metadata_response.trainingMethods.keys()) == 0:
            return False
        n_methods = 0
        for service, methods in metadata_response.trainingMethods.items():
            n_methods += len(methods)
        if n_methods == 0:
            return False
        else:
            return True

    def _check_dataset(self, model_id: str, zip_path: str | Path | PurePath):
        requirements_response = self.get_dataset_requirements("", model_id)
        max_size_mb = requirements_response.max_size_mb
        max_count_files = requirements_response.count_files
        max_size_mb_single = requirements_response.max_size_mb_single
        file_types = requirements_response.file_type

        failed_checks = []
        zip_file = ZipFile(zip_path)

        if os.path.getsize(zip_path) > max_size_mb * 1024 * 1024:
            failed_checks.append(f"Too big dataset size: {os.path.getsize(zip_path)} > {max_size_mb} MB")

        files_list = zip_file.infolist()
        if len(files_list) > max_count_files:
            failed_checks.append(f"Too many files: {len(files_list)} > {max_count_files}")

        for file_info in files_list:
            _, extension = os.path.splitext(file_info.filename)
            if extension not in file_types:
                failed_checks.append(f"Wrong file type: `{extension}` in file: `{file_info.filename}`. Allowed file types: {', '.join(file_types)}")
            if file_info.file_size > max_size_mb_single * 1024 * 1024:
                failed_checks.append(f"Too big file `{file_info.filename}` size: {file_info.file_size / 1024 / 1024} > {max_size_mb_single} MB")

        if len(failed_checks) > 0:
            exception_msg = "Dataset check failed:\n"
            for check in failed_checks:
                exception_msg += f"\t{check}\n"
            raise Exception(exception_msg)

    def _get_grpc_channel(self, base_channel: grpc.Channel) -> grpc.Channel:
        grpc_channel = grpc.intercept_channel(
            base_channel,
            generic_client_interceptor.create(self._intercept_call)
        )
        return grpc_channel

    def _intercept_call(self, client_call_details, request_iterator, request_streaming,
                        response_streaming):
        metadata = []
        if client_call_details.metadata is not None:
            metadata = list(client_call_details.metadata)
        metadata.extend(self.payment_strategy.get_payment_metadata(self.service_client))
        client_call_details = _ClientCallDetails(
            client_call_details.method, client_call_details.timeout, metadata,
            client_call_details.credentials)
        return client_call_details, request_iterator, None

