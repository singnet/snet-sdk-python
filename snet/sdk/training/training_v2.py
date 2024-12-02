import enum
from http.client import responses
from os import PathLike
from pathlib import PurePath, Path
from typing import NewType

from jsonrpcclient import request

from snet.sdk.service_client import ServiceClient

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
        # TODO: store model_id and prices

    # TODO: implement whole process in one method

    """FREE METHODS TO CALL"""

    def create_model(self, method_name: str,
                     model_name: str,
                     model_description: str="",
                     is_public_accessible: bool=False,
                     addresses_with_access: list[str]=None):
        if addresses_with_access is None:
            addresses_with_access = []
        new_model = training.NewModel(name=model_name,
                                      description=model_description,
                                      grpc_method_name=method_name,
                                      grpc_service_name="service", # TODO: get from service_client
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
        # TODO: process response
        return response

    def validate_model_price(self, model_id: int):
        auth_details = self._get_auth_details(ModelMethodMessage.ValidateModelPrice)
        validate_model_price_request = training_daemon.ValidateRequest(
            authorization=auth_details,
            model_id=model_id,
            training_data_link=""
        )
        response = self._call_method("validate_model_price",
                                     request_data=validate_model_price_request)
        # TODO: process response
        return response

    def train_model_price(self, model_id: int):
        auth_details = self._get_auth_details(ModelMethodMessage.TrainModelPrice)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("train_model_price",
                                     request_data=common_request)
        # TODO: process response
        return response

    def delete_model(self, model_id: int):
        auth_details = self._get_auth_details(ModelMethodMessage.DeleteModel)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("delete_model",
                                     request_data=common_request)
        # TODO: process response
        return response

    def get_training_metadata(self):
        response = self._call_method("get_training_metadata")
        # TODO: process response
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
        # TODO: process response
        return response

    def get_model(self, model_id: int):
        auth_details = self._get_auth_details(ModelMethodMessage.GetModel)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("get_model",
                                     request_data=common_request)
        # TODO: process response
        return response

    def update_model(self, model_id: int,
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
        # TODO: process response
        return response

    def get_dataset_requirements(self, method_name: str):
        requirements_request = training_daemon.DatasetRequirementsRequest(
            grpc_method_name=method_name,
            grpc_service_name="service" # TODO: get from service_client
        )
        response = self._call_method("get_dataset_requirements",
                                     request_data=requirements_request)
        # TODO: process response
        return response

    """PAID METHODS TO CALL"""

    def upload_and_validate(self, model_id: int, zip_path: str | Path | PurePath):
        data = []
        with open(zip_path, 'rb') as f: # TODO: handle exceptions with file
            data_part = f.read(256)
            while data_part:
                data.append(data_part)

        auth_details = self._get_auth_details(ModelMethodMessage.UploadAndValidate)

        upload_and_validate_request = []
        for data_part in data:
            upload_and_validate_request.append(
                training_daemon.UploadAndValidateRequest(
                    authorization=auth_details,
                    model_id=model_id,
                    data=data_part)
            )
        upload_and_validate_request = iter(upload_and_validate_request)

        response = self._call_method("upload_and_validate",
                                     request_data=upload_and_validate_request,
                                     paid=True)
        # TODO: process response
        return response

    def train_model(self, model_id: int):
        auth_details = self._get_auth_details(ModelMethodMessage.TrainModel)
        common_request = training_daemon.CommonRequest(authorization=auth_details,
                                                       model_id=model_id)
        response = self._call_method("train_model",
                                     request_data=common_request,
                                     paid=True)
        # TODO: process response
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
            print("Exception: ", e)
            return e

    def _get_training_stub(self, paid=False):
        if paid:
            grpc_channel = self.service_client.grpc_channel
        else:
            grpc_channel = self.service_client.get_grpc_base_channel()
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

