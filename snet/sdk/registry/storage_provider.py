from typing import Any

from lighthouseweb3 import Lighthouse
import json

from snet.sdk.registry.registry_contract import RegistryContract
from snet.sdk.types import StorageType, FileURI
from snet.sdk.utils.ipfs_utils import (
    get_ipfs_client,
    get_from_ipfs_and_checkhash,
)
from snet.sdk.utils.utils import bytesuri_to_hash, safe_extract_proto
from snet.sdk.registry.service_metadata import (
    MPEServiceMetadata,
    mpe_service_metadata_from_json,
)
from snet.sdk.config import config


class StorageProvider(object):
    def __init__(self, registry_contract: RegistryContract):
        self._registry_contract = registry_contract
        self._ipfs_client = get_ipfs_client()
        self.lighthouse_client = Lighthouse(config.LIGHTHOUSE_TOKEN)

    def fetch_org_metadata(self, org_id):
        org = self._registry_contract.get_org(org_id)

        org_metadata_json = self._get_from_storage(org.metadata_uri)
        org_metadata = json.loads(org_metadata_json)

        return org_metadata

    def fetch_service_metadata(self, org_id: str, service_id: str) -> MPEServiceMetadata:
        service = self._registry_contract.get_service(org_id, service_id)

        service_metadata_json = self._get_from_storage(service.metadata_uri)
        service_metadata = mpe_service_metadata_from_json(service_metadata_json)

        return service_metadata

    def enhance_service_metadata(self, org_id, service_id):
        service_metadata = self.fetch_service_metadata(org_id, service_id)
        org_metadata = self.fetch_org_metadata(org_id)

        org_group_map = {}
        for group in org_metadata["groups"]:
            org_group_map[group["group_name"]] = group

        for group in service_metadata.m["groups"]:
            # merge service group with org_group
            group["payment"] = org_group_map[group["group_name"]]["payment"]

        return service_metadata

    def fetch_and_extract_proto(self, service_api_source, proto_dir):
        try:
            tar_uri = bytesuri_to_hash(
                service_api_source, to_decode=False
            )
        except Exception:
            # TODO: change exception based on bytesuri_to_hash function
            tar_uri = FileURI(storage_type = StorageType.IPFS, uri_hash = service_api_source)

        spec_tar = self._get_from_storage(tar_uri)

        safe_extract_proto(spec_tar, proto_dir)

    def _get_from_storage(self, uri: FileURI) -> Any:
        if uri.storage_type == StorageType.IPFS:
            file = get_from_ipfs_and_checkhash(self._ipfs_client, uri.uri_hash)
        elif uri.storage_type == StorageType.FILECOIN:
            file, _ = self.lighthouse_client.download(uri.uri_hash)
        else:
            # TODO: configure exceptions
            raise Exception()

        return file