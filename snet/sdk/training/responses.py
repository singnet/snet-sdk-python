from enum import Enum
from typing import Any


class ModelMethodMessage(Enum):
    CreateModel = "create_model"
    ValidateModelPrice = "validate_model_price"
    TrainModelPrice = "train_model_price"
    DeleteModel = "delete_model"
    GetTrainingMetadata = "get_training_metadata"
    GetAllModels = "get_all_models"
    GetModel = "get_model"
    UpdateModel = "update_model"
    GetMethodMetadata = "get_method_metadata"
    UploadAndValidate = "upload_and_validate"
    ValidateModel = "validate_model"
    TrainModel = "train_model"


class ModelStatus(Enum):
    CREATED = 0
    VALIDATING = 1
    VALIDATED = 2
    TRAINING = 3
    READY_TO_USE = 4
    ERRORED = 5
    DELETED = 6


def to_string(obj: Any):
    res_str = ""
    for key, value in obj.__dict__.items():
        key = key.split("__")[1].replace("_", " ")
        res_str += f"{key}: {value}\n"
    return res_str


class Model:
    def __init__(self, model_response):
        self.__model_id = model_response.model_id
        self.__status = ModelStatus(model_response.status)
        self.__created_date = model_response.created_date
        self.__updated_date = model_response.updated_date
        self.__name = model_response.name
        self.__description = model_response.description
        self.__grpc_method_name = model_response.grpc_method_name
        self.__grpc_service_name = model_response.grpc_service_name
        self.__address_list = model_response.address_list
        self.__is_public = model_response.is_public
        self.__training_data_link = model_response.training_data_link
        self.__created_by_address = model_response.created_by_address
        self.__updated_by_address = model_response.updated_by_address

    def __str__(self):
        return to_string(self)

    @property
    def model_id(self):
        return self.__model_id

    @property
    def status(self):
        return self.__status

    @property
    def created_date(self):
        return self.__created_date

    @property
    def updated_date(self):
        return self.__updated_date

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def grpc_method_name(self):
        return self.__grpc_method_name

    @property
    def grpc_service_name(self):
        return self.__grpc_service_name

    @property
    def address_list(self):
        return self.__address_list

    @property
    def is_public(self):
        return self.__is_public

    @property
    def training_data_link(self):
        return self.__training_data_link

    @property
    def created_by_address(self):
        return self.__created_by_address

    @property
    def updated_by_address(self):
        return self.__updated_by_address


class TrainingMetadata:
    def __init__(self,
                 training_enabled: bool,
                 training_in_proto: bool,
                 training_methods: Any):

        self.__training_enabled = training_enabled
        self.__training_in_proto = training_in_proto
        self.__training_methods = {}

        services_methods = dict(training_methods)
        for k, v in services_methods.items():
            self.__training_methods[k] = [value.string_value for value in v.values]

    def __str__(self):
        return to_string(self)

    @property
    def training_enabled(self):
        return self.__training_enabled

    @property
    def training_in_proto(self):
        return self.__training_in_proto

    @property
    def training_methods(self):
        return self.__training_methods


class MethodMetadata:
    def __init__(self,
                 default_model_id: str,
                 max_models_per_user: int,
                 dataset_max_size_mb: int,
                 dataset_max_count_files: int,
                 dataset_max_size_single_file_mb: int,
                 dataset_files_type: str,
                 dataset_type: str,
                 dataset_description: str):

        self.__default_model_id = default_model_id
        self.__max_models_per_user = max_models_per_user
        self.__dataset_max_size_mb = dataset_max_size_mb
        self.__dataset_max_count_files = dataset_max_count_files
        self.__dataset_max_size_single_file_mb = dataset_max_size_single_file_mb
        self.__dataset_files_type = dataset_files_type
        self.__dataset_type = dataset_type
        self.__dataset_description = dataset_description

    def __str__(self):
        return to_string(self)

    @property
    def default_model_id(self):
        return self.__default_model_id

    @property
    def max_models_per_user(self):
        return self.__max_models_per_user

    @property
    def dataset_max_size_mb(self):
        return self.__dataset_max_size_mb

    @property
    def dataset_max_count_files(self):
        return self.__dataset_max_count_files

    @property
    def dataset_max_size_single_file_mb(self):
        return self.__dataset_max_size_single_file_mb

    @property
    def dataset_files_type(self):
        return self.__dataset_files_type

    @property
    def dataset_type(self):
        return self.__dataset_type

    @property
    def dataset_description(self):
        return self.__dataset_description


