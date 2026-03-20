import io
import tarfile
from pathlib import Path
from typing import Union

import ipfshttpclient
from lighthouseweb3 import Lighthouse
import json
import multihash
import hashlib

from snet.sdk.registry.registry_contract import RegistryContract
from snet.sdk.registry.models import StorageType, FileURI
from snet.sdk.registry.service_metadata import (
    MPEServiceMetadata,
    mpe_service_metadata_from_json,
)
from snet.sdk.config import config


class StorageProvider(object):
    def __init__(self, registry_contract: RegistryContract):
        self._registry_contract = registry_contract
        self._ipfs_client = ipfshttpclient.connect(config.IPFS_ENDPOINT)
        self._lighthouse_client = Lighthouse(config.LIGHTHOUSE_TOKEN)

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
        tar_uri = FileURI.from_raw_uri(service_api_source)
        spec_tar = self._get_from_storage(tar_uri)
        self.safe_extract_proto(spec_tar, proto_dir)

    def _get_from_storage(self, uri: FileURI, decode: bool = True) -> Union[bytes, str]:
        match uri.storage_type:
            case StorageType.IPFS:
                file = self._get_from_ipfs_and_checkhash(uri.uri_hash)
            case StorageType.FILECOIN:
                file, _ = self._lighthouse_client.download(uri.uri_hash)
            case _:
                raise ValueError(f"Unsupported storage type: {uri.storage_type}")
        if decode:
            file = file.decode()
        return file

    def _get_from_ipfs_and_checkhash(self, ipfs_hash: str, validate: bool = False) -> bytes:
        data = self._ipfs_client.cat(ipfs_hash)

        if validate:
            block_data = self._ipfs_client.block.get(ipfs_hash)

            try:
                mh_bytes = multihash.from_b58_string(ipfs_hash)
                decoded = multihash.decode(mh_bytes)

                hash_func_name = decoded.name
                expected_digest = decoded.digest

                if hash_func_name == "sha2-256":
                    actual_digest = hashlib.sha256(block_data).digest()
                else:
                    h = hashlib.new(hash_func_name.replace("-", ""))
                    h.update(block_data)
                    actual_digest = h.digest()

                if actual_digest != expected_digest:
                    raise Exception("IPFS hash mismatch with data")

            except Exception as e:
                raise ValueError(f"Integrity check failed: {str(e)}") from e

        return data

    @staticmethod
    def safe_extract_proto(spec_tar: bytes, proto_dir: Union[str, Path]) -> None:
        dest_dir = Path(proto_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(fileobj=io.BytesIO(spec_tar)) as f:
            valid_members = []

            for m in f.getmembers():
                if not m.isfile():
                    raise ValueError(
                        f"Security/Format Error: Tarball contains a non-file item: '{m.name}'"
                    )
                if Path(m.name).parent != Path("."):
                    raise ValueError(
                        f"Format Error: Tarball contains nested paths ('{m.name}'). Only flat archives are supported."
                    )
                if not m.name.endswith(".proto"):
                    raise ValueError(
                        f"Format Error: Unexpected file type '{m.name}'. Only .proto files allowed."
                    )
                target_file = dest_dir / m.name
                if target_file.exists():
                    target_file.unlink()
                    print(f"Removed existing file: {target_file}")
                valid_members.append(m)

            f.extractall(path=dest_dir, members=valid_members, filter="data")
