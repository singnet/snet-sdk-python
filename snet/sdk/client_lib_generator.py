import os
from pathlib import Path, PurePath

from snet.sdk.utils import ipfs_utils
from snet.sdk.utils.utils import compile_proto, type_converter
from snet.sdk.metadata_provider.service_metadata import mpe_service_metadata_from_json


class ClientLibGenerator:

    def __init__(self, sdk_config, registry_contract, org_id, service_id):
        self.sdk_config = sdk_config
        self.registry_contract = registry_contract
        self.org_id = org_id
        self.service_id = service_id
        self.language = "python"
        self.protodir = Path("~").expanduser().joinpath(".snet")

    def generate_client_library(self):

        if os.path.isabs(self.protodir):
            client_libraries_base_dir_path = PurePath(self.protodir)
        else:
            cur_dir_path = PurePath(os.getcwd())
            client_libraries_base_dir_path = cur_dir_path.joinpath(self.protodir)

        os.makedirs(client_libraries_base_dir_path, exist_ok=True)

        # Create service client libraries path
        library_language = self.language
        library_org_id = self.org_id
        library_service_id = self.service_id

        library_dir_path = client_libraries_base_dir_path.joinpath(library_org_id,
                                                                   library_service_id,
                                                                   library_language)

        try:
            metadata = self._get_service_metadata_from_registry()
            model_ipfs_hash = metadata["model_ipfs_hash"]

            # Receive proto files
            ipfs_utils.safe_extract_proto_from_ipfs(ipfs_utils.get_ipfs_client(self.sdk_config),
                                                    model_ipfs_hash, library_dir_path)

            # Compile proto files
            compile_proto(Path(library_dir_path), library_dir_path, target_language=self.language)

            print(f'client libraries for service with id "{library_service_id}" in org with id "{library_org_id}" '
                  f'generated at {library_dir_path}')
        except Exception as e:
            print(e)

    def _get_service_metadata_from_registry(self):
        rez = self._get_service_registration()
        metadata_hash = ipfs_utils.bytesuri_to_hash(rez["metadataURI"])
        metadata = ipfs_utils.get_from_ipfs_and_checkhash(ipfs_utils.get_ipfs_client(self.sdk_config), metadata_hash)
        metadata = metadata.decode("utf-8")
        metadata = mpe_service_metadata_from_json(metadata)
        return metadata

    def _get_service_registration(self):
        params = [type_converter("bytes32")(self.org_id), type_converter("bytes32")(self.service_id)]
        rez = self.registry_contract.functions.getServiceRegistrationById(*params).call()
        if not rez[0]:
            raise Exception("Cannot find Service with id=%s in Organization with id=%s" % (
                self.service_id, self.org_id))
        return {"metadataURI": rez[2]}


