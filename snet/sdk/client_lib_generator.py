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
        self.library_dir_path: Path | None = None

    def generate_directory_by_params(self) -> None:
        if self.protodir.is_absolute():
            base_dir_path = Path(self.protodir)
        else:
            base_dir_path = Path.cwd().joinpath(self.protodir)

        base_dir_path.mkdir(exist_ok=True)

        # Create service client libraries path
        self.library_dir_path = base_dir_path.joinpath(self.org_id,
                                                       self.service_id,
                                                       self.language)
        self.library_dir_path.mkdir(parents=True, exist_ok=True)

    def receive_proto_files(self) -> None:
        metadata = self._metadata_provider.fetch_service_metadata(
            self.org_id,
            self.service_id
        )
        service_api_source = (metadata.get("service_api_source") or
                              metadata.get("model_ipfs_hash"))

        # Receive proto files
        if self.library_dir_path.exists():
            self._metadata_provider.fetch_and_extract_proto(
                service_api_source,
                self.library_dir_path
            )
        else:
            raise Exception("Directory for storing proto files not found")

    def generate_client_library(self) -> None:
        try:
            self.generate_directory_by_params()
            self.receive_proto_files()
            compile_proto(self.library_dir_path,
                          self.library_dir_path,
                          target_language=self.language)

            print(f'client libraries for service with id "{self.service_id}" '
                  f'in org with id "{self.org_id}" '
                  f'generated at {self.library_dir_path}')
        except Exception as e:
            print(e)
