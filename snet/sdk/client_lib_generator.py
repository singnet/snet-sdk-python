import os
from pathlib import Path

from snet.sdk.storage_provider.storage_provider import StorageProvider
from snet.sdk.utils.utils import compile_proto


class ClientLibGenerator:
    def __init__(self, metadata_provider: StorageProvider, org_id: str,
                 service_id: str, protodir: Path | None = None):
        self._metadata_provider: StorageProvider = metadata_provider
        self.org_id: str = org_id
        self.service_id: str = service_id
        self.language: str = "python"
        self.protodir: Path = (protodir if protodir else
                               Path.home().joinpath(".snet"))
        self.generate_directories_by_params()

    def generate_client_library(self) -> None:
        try:
            self.receive_proto_files()
            compilation_result = compile_proto(entry_path=self.protodir,
                                               codegen_dir=self.protodir,
                                               target_language=self.language,
                                               add_training=self.training_added())
            if compilation_result:
                print(f'client libraries for service with id "{self.service_id}" '
                      f'in org with id "{self.org_id}" '
                      f'generated at {self.protodir}')
        except Exception as e:
            print(str(e))

    def generate_directories_by_params(self) -> None:
        if not self.protodir.is_absolute():
            self.protodir = Path.cwd().joinpath(self.protodir)
        self.create_service_client_libraries_path()

    def create_service_client_libraries_path(self) -> None:
        self.protodir = self.protodir.joinpath(self.org_id,
                                               self.service_id,
                                               self.language)
        self.protodir.mkdir(parents=True, exist_ok=True)

    def receive_proto_files(self) -> None:
        metadata = self._metadata_provider.fetch_service_metadata(
            org_id=self.org_id,
            service_id=self.service_id
        )
        service_api_source = (metadata.get("service_api_source") or
                              metadata.get("model_ipfs_hash"))

        # Receive proto files
        if self.protodir.exists():
            self._metadata_provider.fetch_and_extract_proto(
                service_api_source,
                self.protodir
            )
        else:
            raise Exception("Directory for storing proto files is not found")

    def training_added(self) -> bool:
        files = os.listdir(self.protodir)
        for file in files:
            if ".proto" not in file:
                continue
            with open(self.protodir.joinpath(file), "r") as f:
                proto_text = f.read()
            if 'import "training.proto";' in proto_text:
                return True
        return False
