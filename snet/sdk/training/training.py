from pathlib import PurePath, Path
import os
from zipfile import ZipFile
from typing import Any
import grpc
import importlib

from snet.sdk import generic_client_interceptor
from snet.sdk.payment_strategies.training_payment_strategy import TrainingPaymentStrategy
from snet.sdk.utils.call_utils import create_intercept_call_func
from snet.sdk.utils.utils import add_to_path, RESOURCES_PATH
from snet.sdk.training.exceptions import (
    WrongDatasetException,
    WrongMethodException,
    GRPCException,
    NoSuchModelException
)
from snet.sdk.training.responses import (
    ModelStatus,
    Model,
    TrainingMetadata,
    MethodMetadata,
    ModelMethodMessage
)


class Training:
    def __init__(self, service_client, training_added=False):
        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            self.training_daemon = importlib.import_module("training_daemon_pb2")
            self.training_daemon_grpc = importlib.import_module("training_daemon_pb2_grpc")
            self.training = importlib.import_module("training_pb2")
            
        self.service_client = service_client
        self.is_enabled = training_added and self._check_training()
        self.payment_strategy = TrainingPaymentStrategy()

    def get_model_id_object(self, model_id: str) -> Any:
        return self.training.ModelID(model_id=model_id)

    """FREE METHODS TO CALL"""

    def create_model(self, method_name: str,
                     model_name: str,
                     model_description: str="",
                     is_public_accessible: bool=False,
                     addresses_with_access: list[str]=None) -> Model:
        if addresses_with_access is None:
            addresses_with_access = []

        service_name, method_name = self._check_method_name(method_name)
        new_model = self.training.NewModel(name=model_name,
                                      description=model_description,
                                      grpc_method_name=method_name,
                                      grpc_service_name=service_name,
                                      is_public=is_public_accessible,
                                      address_list=addresses_with_access,
                                      organization_id="",
                                      service_id="",
                                      group_id="")
        auth_details = self._get_auth_details(ModelMethodMessage.CreateModel)
        create_model_request = self.training_daemon.NewModelRequest(authorization=auth_details,
                                                               model=new_model)
        response = self._call_method("create_model",
                                     request_data=create_model_request)
        model = Model(response)

        return model

    def validate_model_price(self, model_id: str) -> int:
        auth_details = self._get_auth_details(ModelMethodMessage.ValidateModelPrice)
        validate_model_price_request = self.training_daemon.AuthValidateRequest(
            authorization=auth_details,
            model_id=model_id,
            training_data_link=""
        )

        try:
            response = self._call_method("validate_model_price",
                                         request_data=validate_model_price_request)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e

        return response.price

    def train_model_price(self, model_id: str) -> int:
        auth_details = self._get_auth_details(ModelMethodMessage.TrainModelPrice)
        common_request = self.training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        try:
            response = self._call_method("train_model_price",
                                         request_data=common_request)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e

        return response.price

    def delete_model(self, model_id: str) -> ModelStatus:
        auth_details = self._get_auth_details(ModelMethodMessage.DeleteModel)
        common_request = self.training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        try:
            response = self._call_method("delete_model",
                                         request_data=common_request)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e

        return ModelStatus(response.status)

    def get_training_metadata(self) -> TrainingMetadata:
        empty_request = self.training_daemon.google_dot_protobuf_dot_empty__pb2.Empty()
        response = self._call_method("get_training_metadata",
                                     request_data=empty_request)

        training_metadata = TrainingMetadata(training_enabled=response.trainingEnabled,
                                             training_in_proto=response.trainingInProto,
                                             training_methods=response.trainingMethods)

        return training_metadata

    def get_all_models(self, statuses: list[ModelStatus]=None,
                       is_public: bool=None,
                       grpc_method_name: str="",
                       grpc_service_name: str="",
                       model_name: str="",
                       created_by_address: str="") -> list[Model]:
        if statuses is not None:
            statuses = [getattr(self.training.Status, status.value) for status in statuses]
        auth_details = self._get_auth_details(ModelMethodMessage.GetAllModels)
        all_models_request = self.training_daemon.AllModelsRequest(
            authorization=auth_details,
            statuses=statuses,
            is_public=is_public,
            grpc_method_name=grpc_method_name,
            grpc_service_name=grpc_service_name,
            name=model_name,
            created_by_address=created_by_address,
            page_size=0,
            page=0
        )
        response = self._call_method("get_all_models",
                                     request_data=all_models_request)
        models = []
        for model in response.list_of_models:
            models.append(Model(model))

        return models

    def get_model(self, model_id: str) -> Model:
        auth_details = self._get_auth_details(ModelMethodMessage.GetModel)
        common_request = self.training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        try:
            response = self._call_method("get_model",
                                         request_data=common_request)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e
        model = Model(response)

        return model

    def get_method_metadata(self, method_name: str, model_id: str= "") -> MethodMetadata:

        if model_id:
            requirements_request = self.training_daemon.MethodMetadataRequest(
                grpc_method_name="",
                grpc_service_name="",
                model_id=model_id
            )
        else:
            service_name, method_name = self._check_method_name(method_name)
            requirements_request = self.training_daemon.MethodMetadataRequest(
                grpc_method_name=method_name,
                grpc_service_name=service_name,
                model_id=""
            )
        response = self._call_method("get_method_metadata",
                                     request_data=requirements_request)

        method_metadata = MethodMetadata(default_model_id = response.default_model_id,
                                         max_models_per_user = response.max_models_per_user,
                                         dataset_max_size_mb = response.dataset_max_size_mb,
                                         dataset_max_count_files = response.dataset_max_count_files,
                                         dataset_max_size_single_file_mb = response.dataset_max_size_single_file_mb,
                                         dataset_files_type = response.dataset_files_type,
                                         dataset_type = response.dataset_type,
                                         dataset_description = response.dataset_description)
        return method_metadata

    def update_model(self, model_id: str,
                     model_name: str=None,
                     description: str=None,
                     addresses_with_access: list[str]=None) -> Model:
        auth_details = self._get_auth_details(ModelMethodMessage.UpdateModel)
        update_model_request = self.training_daemon.UpdateModelRequest(
            authorization=auth_details,model_id=model_id,
            model_name=model_name,
            description=description,
            address_list=addresses_with_access
        )

        try:
            response = self._call_method("update_model",
                                         request_data=update_model_request)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e

        model = Model(response)

        return model

    """PAID METHODS TO CALL"""

    def upload_and_validate(self, model_id: str,
                            zip_path: str | Path | PurePath, price: int) -> ModelStatus:
        f = open(zip_path, 'rb')
        file_size = os.path.getsize(zip_path)

        file_name = os.path.basename(zip_path)
        file_size = file_size
        batch_size = 1024*1024
        batch_count = file_size // batch_size
        if file_size % batch_size != 0:
            batch_count += 1

        self._check_dataset(model_id, zip_path)

        auth_details = self._get_auth_details(ModelMethodMessage.UploadAndValidate)

        def request_iter(file):
            batch = file.read(batch_size)
            batch_number = 1
            while batch:
                upload_input = self.training.UploadInput(
                    model_id = model_id,
                    data = batch,
                    file_name = file_name,
                    file_size = file_size,
                    batch_size = batch_size,
                    batch_number = batch_number,
                    batch_count = batch_count
                )
                yield self.training_daemon.UploadAndValidateRequest(
                    authorization=auth_details,
                    upload_input=upload_input
                )
                batch = file.read(batch_size)
                batch_number += 1

        self.payment_strategy.set_price(price)
        self.payment_strategy.set_model_id(model_id)

        try:
            response = self._call_method("upload_and_validate",
                                         request_data=request_iter(f),
                                         paid=True)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e
        finally:
            f.close()

        return ModelStatus(response.status)

    def train_model(self, model_id: str, price: int) -> ModelStatus:
        auth_details = self._get_auth_details(ModelMethodMessage.TrainModel)
        common_request = self.training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        self.payment_strategy.set_price(price)
        self.payment_strategy.set_model_id(model_id)

        try:
            response = self._call_method("train_model",
                                         request_data=common_request,
                                         paid=True)
        except GRPCException as e:
            if "unable to access model" in str(e):
                raise NoSuchModelException(model_id)
            else:
                raise e

        return ModelStatus(response.status)

    """PRIVATE METHODS"""

    def _call_method(self, method_name: str,
                     request_data,
                     paid=False) -> Any:
        try:
            stub = self._get_training_stub(paid=paid)
            response = getattr(stub, method_name)(request_data)
            return response
        except grpc.RpcError as e:
            raise GRPCException(e)

    def _get_training_stub(self, paid=False) -> Any:
        grpc_channel = self.service_client.get_grpc_base_channel()
        if paid:
            grpc_channel = self._get_grpc_channel(grpc_channel)
        return self.training_daemon_grpc.DaemonStub(grpc_channel)

    def _get_auth_details(self, method_msg: ModelMethodMessage) -> Any:
        current_block_number = self.service_client.get_current_block_number()
        address = self.service_client.account.address
        signature = self.service_client.generate_training_signature(method_msg.value,
                                                                    address,
                                                                    current_block_number)
        auth_details = self.training_daemon.AuthorizationDetails(
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
        raise WrongMethodException(method_name)

    def _check_training(self) -> bool:
        try:
            service_methods = self.get_training_metadata().training_methods
        except GRPCException as e:
            return False
        if len(service_methods.keys()) == 0:
            return False
        n_methods = 0
        for service, methods in service_methods.items():
            n_methods += len(methods)
        if n_methods == 0:
            return False
        else:
            return True

    def _check_dataset(self, model_id: str, zip_path: str | Path | PurePath) -> None:
        method_metadata = self.get_method_metadata("", model_id)
        max_size_mb = method_metadata.dataset_max_size_mb
        max_count_files = method_metadata.dataset_max_count_files
        max_size_mb_single = method_metadata.dataset_max_size_single_file_mb
        file_types = method_metadata.dataset_files_type
        file_types = [i for i in file_types.replace(' ', '').split(',')]
        if file_types[0] == '':
            file_types = []

        failed_checks = []
        zip_file = ZipFile(zip_path)

        if os.path.getsize(zip_path) > max_size_mb * 1024 * 1024 > 0:
            failed_checks.append(f"Too big dataset size: "
                                 f"{os.path.getsize(zip_path)//1024/1024} MB > {max_size_mb} MB")

        files_list = zip_file.infolist()
        if len(files_list) > max_count_files > 0:
            failed_checks.append(f"Too many files: {len(files_list)} > {max_count_files}")

        for file_info in files_list:
            _, extension = os.path.splitext(file_info.filename)
            extension = extension[1:] if extension.startswith('.') else extension
            if len(file_types) > 0 and extension not in file_types:
                failed_checks.append(f"Wrong file type: `{extension}` in file: "
                                     f"`{file_info.filename}`. Allowed file types: "
                                     f"{', '.join(file_types)}")
            if file_info.file_size > max_size_mb_single * 1024 * 1024 > 0:
                failed_checks.append(f"Too big file `{file_info.filename}` size: "
                                     f"{file_info.file_size // 1024 / 1024} MB > "
                                     f"{max_size_mb_single} MB")

        if len(failed_checks) > 0:
            raise WrongDatasetException(failed_checks)

    def _get_grpc_channel(self, base_channel: grpc.Channel) -> grpc.Channel:
        intercept_call_func = create_intercept_call_func(self.payment_strategy.get_payment_metadata,
                                                         self.service_client)
        grpc_channel = grpc.intercept_channel(
            base_channel,
            generic_client_interceptor.create(intercept_call_func)
        )
        return grpc_channel
