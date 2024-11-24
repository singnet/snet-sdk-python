import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, Mock, patch

from snet.sdk.client_lib_generator import ClientLibGenerator
from snet.sdk.storage_provider.storage_provider import StorageProvider


class TestClientLibGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_metadata_provider = Mock(spec=StorageProvider)
        self.org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
        self.service_id = "Exampleservice"
        self.language = "python"
        self.protodir = Path.home().joinpath(".snet1")
        self.generator = ClientLibGenerator(
            metadata_provider=self.mock_metadata_provider,
            org_id=self.org_id,
            service_id=self.service_id,
            protodir=self.protodir
        )

    @patch("pathlib.Path.mkdir")
    def test_generate_directories_by_params(self, mock_mkdir):
        expected_library_dir = self.protodir.joinpath(
            self.org_id, self.service_id, self.language
        )
        self.generator.generate_directories_by_params()
        self.assertEqual(self.generator.protodir, expected_library_dir)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_receive_proto_files_success(self):
        # Set up mocks
        mock_metadata = {"service_api_source": None,
                         "model_ipfs_hash": os.getenv("MODEL_IPFS_HASH")}
        self.mock_metadata_provider.fetch_service_metadata \
            .return_value = mock_metadata
        self.generator.protodir = Mock()
        self.generator.protodir.exists.return_value = True

        # Call the method
        self.generator.receive_proto_files()

        # Check method calls
        service_api_source = (mock_metadata.get("service_api_source") or
                              mock_metadata.get("model_ipfs_hash"))
        self.mock_metadata_provider.fetch_service_metadata \
            .assert_called_once_with(
                org_id=self.org_id,
                service_id=self.service_id
            )
        self.mock_metadata_provider.fetch_and_extract_proto \
            .assert_called_once_with(
                service_api_source,
                self.generator.protodir
            )

    def test_receive_proto_files_failed(self):
        self.generator.protodir = Mock()
        self.generator.protodir.exists.return_value = False

        with self.assertRaises(Exception) as context:
            self.generator.receive_proto_files()

        self.assertEqual(str(context.exception),
                         "Directory for storing proto files not found")

    # @patch("snet.sdk.utils.utils.compile_proto")
    # @patch("snet.sdk.client_lib_generator.ClientLibGenerator.generate_directories_by_params")
    # @patch("snet.sdk.client_lib_generator.ClientLibGenerator.receive_proto_files")
    # @patch("pathlib.Path.exists")
    # @patch("pathlib.Path.mkdir")
    # @patch("snet.sdk.client_lib_generator.StorageProvider.fetch_and_extract_proto")
    # def test_generate_client_library_success(self,
    #                                         mock_fetch_and_extract_proto,
    #                                         mock_mkdir,
    #                                         mock_exists,
    #                                         mock_receive_proto_files,
    #                                         mock_generate_directories_by_params,
    #                                         mock_compile_proto):
    #     # Мокаем директорию и путь
    #     # self.generator.protodir = Mock()
    #     # self.generator.protodir.exists.return_value = True
    #     mock_base_dir = MagicMock(spec=Path)
    #     mock_service_dir = MagicMock(spec=Path)
    #     example_proto_file = mock_service_dir.joinpath("example_service.proto")
        
    #     # Убедимся, что директория существует
    #     mock_exists.return_value = True
        
    #     # Подменяем возвращаемое значение при вызове joinpath
    #     mock_base_dir.joinpath.return_value = mock_service_dir
    #     mock_service_dir.joinpath.return_value = example_proto_file
    #     mock_service_dir.exists.return_value = True  # Прототипный файл существует

    #     # Настроим mock для метода fetch_and_extract_proto
    #     mock_fetch_and_extract_proto.return_value = None  # Симулируем успешный экстракт

    #     # Настроим генератор
    #     self.generator.protodir = mock_base_dir
    #     self.generator.protodir.joinpath.return_value = mock_service_dir  # Возвращаем mock для директории сервиса

    #     # Настроим моки для вызова методов
    #     mock_generate_directories_by_params.return_value = None
    #     mock_receive_proto_files.return_value = None

    #     # Запускаем метод
    #     self.generator.generate_client_library()

    #     # Проверяем, что директории и файл созданы
    #     mock_generate_directories_by_params.assert_called_once()
    #     mock_receive_proto_files.assert_called_once()
        
    #     # Убедимся, что compile_proto получил правильный путь
    #     mock_compile_proto.assert_called_once_with(
    #         entry_path=str(mock_service_dir),
    #         codegen_dir=str(mock_service_dir),
    #         target_language="python"
    #     )

    @patch("builtins.print")
    def test_generate_client_library_handles_exception(self, mock_print):
        with patch("snet.sdk.client_lib_generator.ClientLibGenerator.generate_directories_by_params",   # noqa E501
                   side_effect=Exception("Test exception")):
            self.generator.generate_client_library()
            mock_print.assert_called_once_with("Test exception")


if __name__ == '__main__':
    unittest.main()
