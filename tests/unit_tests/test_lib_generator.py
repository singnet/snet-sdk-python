import os
from pathlib import Path
import unittest

from dotenv import load_dotenv

from snet import sdk
from snet.sdk.client_lib_generator import ClientLibGenerator
from snet.sdk.utils.utils import compile_proto

load_dotenv()

config = sdk.config.Config(private_key=os.getenv("PRIVATE_KEY"),
                           eth_rpc_endpoint=os.getenv("INFURA_LINK"),
                           concurrency=False,
                           force_update=False)

snet_sdk = sdk.SnetSDK(config)
protodir = Path.home().joinpath(".snet_test")
org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
service_id = "Exampleservice"
proto_filename = "example_service.proto"
pb2_filename = "example_service_pb2.py"
pb2_grpc_filename = "example_service_pb2_grpc.py"
lib_generator = ClientLibGenerator(
    metadata_provider=snet_sdk._metadata_provider,
    org_id=org_id,
    service_id=service_id,
    protodir=protodir
)


def delete_directory_and_clean_lib_generator(
    lib_generator: ClientLibGenerator
) -> None:
    directory = lib_generator.protodir
    delete_directory_recursive(directory)
    lib_generator.library_dir_path = None


def delete_directory_recursive(directory: Path) -> None:
    if directory.exists() and directory.is_dir():
        for item in directory.iterdir():
            if item.is_dir():
                delete_directory_recursive(item)
            else:
                item.unlink()
        directory.rmdir()
    else:
        print(f"The directory {directory} doesn't exist or isn't a folder.")


def find_file_in_directory(directory: Path, file_name: str) -> bool:
    if directory.exists() and directory.is_dir():
        for item in directory.iterdir():
            if item.is_file() and item.name == file_name:
                return True
    return False


class TestClientLibGenerator(unittest.TestCase):
    def test_generate_directories_by_params(self):
        global lib_generator
        lib_generator.generate_directory_by_params()
        self.assertTrue(lib_generator.protodir.exists())
        self.assertTrue(lib_generator.protodir.is_dir())
        delete_directory_and_clean_lib_generator(lib_generator)

    def test_receive_proto_files(self):
        global lib_generator, proto_filename
        lib_generator.generate_directory_by_params()
        lib_generator.receive_proto_files()
        proto_file = lib_generator.library_dir_path.joinpath(proto_filename)
        self.assertTrue(proto_file.exists())
        self.assertTrue(proto_file.is_file())
        delete_directory_and_clean_lib_generator(lib_generator)

    def test_compile_proto(self):
        global lib_generator, pb2_filename, pb2_grpc_filename
        lib_generator.generate_directory_by_params()
        lib_generator.receive_proto_files()
        compile_proto(entry_path=lib_generator.library_dir_path,
                      codegen_dir=lib_generator.library_dir_path,
                      target_language=lib_generator.language)
        self.assertTrue(find_file_in_directory(lib_generator.library_dir_path,
                                               pb2_filename))
        self.assertTrue(find_file_in_directory(lib_generator.library_dir_path,
                                               pb2_grpc_filename))
        delete_directory_and_clean_lib_generator(lib_generator)

    def test_zzz(self):
        global lib_generator
        with self.assertRaises(Exception):
            lib_generator.receive_proto_files()
            delete_directory_and_clean_lib_generator(lib_generator)
            # I stopped here
            # Need to change name of library_dir_path param


if __name__ == '__main__':
    unittest.main()
