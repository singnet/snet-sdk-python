from lighthouseweb3 import Lighthouse
import json

from snet.sdk.registry.registry_contract import RegistryContract
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
        org_metadata_uri, _, _, _ = self._registry_contract.get_org(org_id)
        org_provider_type, org_metadata_hash = bytesuri_to_hash(org_metadata_uri)

        if org_provider_type == "ipfs":
            org_metadata_json = get_from_ipfs_and_checkhash(self._ipfs_client, org_metadata_hash)
        else:
            org_metadata_json, _ = self.lighthouse_client.download(org_metadata_hash)
        org_metadata = json.loads(org_metadata_json)

        return org_metadata

    def fetch_service_metadata(self, org_id: str, service_id: str) -> MPEServiceMetadata:
        service_metadata_uri = self._registry_contract.get_service(org_id, service_id)
        service_provider_type, service_metadata_hash = bytesuri_to_hash(s=service_metadata_uri)

        if service_provider_type == "ipfs":
            service_metadata_json = get_from_ipfs_and_checkhash(
                self._ipfs_client, service_metadata_hash
            )
        else:
            service_metadata_json, _ = self.lighthouse_client.download(cid=service_metadata_hash)
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

    def fetch_and_extract_proto(self, service_api_source, protodir):
        try:
            proto_provider_type, service_api_source = bytesuri_to_hash(
                service_api_source, to_decode=False
            )
        except Exception:
            proto_provider_type = "ipfs"

        if proto_provider_type == "ipfs":
            spec_tar = get_from_ipfs_and_checkhash(self._ipfs_client, service_api_source)
        else:
            spec_tar, _ = self.lighthouse_client.download(service_api_source)

        safe_extract_proto(spec_tar, protodir)
