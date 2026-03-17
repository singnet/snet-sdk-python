import os
from pathlib import Path

from snet.sdk.registry.storage_provider import StorageProvider
from snet.sdk.utils.utils import compile_proto


class ClientLibGenerator:
    def __init__(
        self,
        metadata_provider: StorageProvider,
        org_id: str,
        service_id: str,
        proto_dir: Path | None = None,
    ):
        self._metadata_provider: StorageProvider = metadata_provider
        self.org_id: str = org_id
        self.service_id: str = service_id
        self.language: str = "python"
        self.proto_dir: Path = proto_dir if proto_dir else Path.home().joinpath(".snet")
        self.generate_directories_by_params()

    def generate_client_library(self) -> None:
        try:
            self.receive_proto_files()
            compilation_result = compile_proto(
                entry_path=self.proto_dir,
                codegen_dir=self.proto_dir,
                target_language=self.language,
                add_training=self.training_added(),
            )
            if compilation_result:
                print(
                    f'client libraries for service with id "{self.service_id}" '
                    f'in org with id "{self.org_id}" '
                    f"generated at {self.proto_dir}"
                )
        except Exception as e:
            print(str(e))

    def generate_directories_by_params(self) -> None:
        if not self.proto_dir.is_absolute():
            self.proto_dir = Path.cwd().joinpath(self.proto_dir)
        self.create_service_client_libraries_path()

    def create_service_client_libraries_path(self) -> None:
        self.proto_dir = self.proto_dir.joinpath(self.org_id, self.service_id, self.language)
        self.proto_dir.mkdir(parents=True, exist_ok=True)

    def receive_proto_files(self) -> None:
        metadata = self._metadata_provider.fetch_service_metadata(
            org_id=self.org_id, service_id=self.service_id
        )
        service_api_source = metadata.get("service_api_source") or metadata.get("model_ipfs_hash")

        # Receive proto files
        if self.proto_dir.exists():
            self._metadata_provider.fetch_and_extract_proto(service_api_source, self.proto_dir)
        else:
            raise Exception("Directory for storing proto files is not found")

    def training_added(self) -> bool:
        files = os.listdir(self.proto_dir)
        for file in files:
            if ".proto" not in file:
                continue
            with open(self.proto_dir.joinpath(file), "r") as f:
                proto_text = f.read()
            if 'import "training.proto";' in proto_text:
                return True
        return False
