import os.path
import unittest
from unittest.mock import patch, MagicMock

from snet.sdk.training.responses import MethodMetadata
from snet.sdk.training.training import Training
from snet.sdk.service_client import ServiceClient
from snet.sdk.training.exceptions import WrongDatasetException


class TestTrainingV2(unittest.TestCase):
    def setUp(self):
        self.mock_service_client = MagicMock(spec=ServiceClient)
        self.training = Training(self.mock_service_client, training_added=True)
        self.file_path = os.path.join(os.path.dirname(__file__), "test_files.zip")
        self.get_metadata_path = "snet.sdk.training.training_v2.TrainingV2.get_method_metadata"

    def test_check_dataset_positive(self):
        method_metadata = MethodMetadata("test",
                                         5,
                                         50,
                                         10,
                                         25,
                                         "jpg, png, wav",
                                         "zip",
                                         "test")

        with patch(self.get_metadata_path, return_value=method_metadata):
            try:
                self.training._check_dataset("test", self.file_path)
            except WrongDatasetException as e:
                print(e)
                assert False
            assert True

    def test_check_dataset_negative(self):
        method_metadata = MethodMetadata("test",
                                         5,
                                         10,
                                         10,
                                         5,
                                         "png, mp3, txt",
                                         "zip",
                                         "test")

        with patch(self.get_metadata_path, return_value=method_metadata):
            with self.assertRaises(WrongDatasetException):
                self.training._check_dataset("test", self.file_path)
