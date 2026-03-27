import io
import tarfile
import tempfile
from pathlib import Path
from typing import Union

import ipfshttpclient
from lighthouseweb3 import Lighthouse
import json
import multihash
import hashlib

from snet.sdk.exceptions import (
    UnsupportedStorageTypeError,
    LighthouseError,
    WrongDirectoryError,
    ProtoFilesNotFoundError,
    IPFSHashMismatchError,
    IPFSHashCheckError,
    ExtractingProtoError,
)
from snet.sdk.registry.organization_metadata import OrganizationMetadata
from snet.sdk.registry.models import StorageType, FileURI
from snet.sdk.registry.service_metadata import ServiceMetadata
from snet.sdk.config import config


class StorageProvider(object):
    def __init__(self):
        self._ipfs_client = ipfshttpclient.connect(config.IPFS_ENDPOINT)
        self._lighthouse_client = Lighthouse(config.LIGHTHOUSE_TOKEN)

    def fetch_org_metadata(self, metadata_uri: FileURI) -> OrganizationMetadata:
        org_metadata_json = self._get_from_storage(metadata_uri)
        raw_org_metadata = json.loads(org_metadata_json)
        org_metadata = OrganizationMetadata(**raw_org_metadata)

        return org_metadata

    def fetch_service_metadata(self, metadata_uri: FileURI) -> ServiceMetadata:
        service_metadata_json = self._get_from_storage(metadata_uri)
        raw_service_metadata = json.loads(service_metadata_json)
        service_metadata = ServiceMetadata(**raw_service_metadata)

        return service_metadata

    def fetch_and_extract_proto(self, service_api_source, proto_dir) -> None:
        tar_uri = FileURI.from_raw_uri(service_api_source)
        spec_tar = self._get_from_storage(tar_uri)
        self._safe_extract_proto(spec_tar, proto_dir)

    def publish_organization_metadata(
        self,
        organization_metadata: OrganizationMetadata,
        storage_type: StorageType = StorageType.IPFS,
    ) -> FileURI:
        return self._publish_metadata(
            organization_metadata, storage_type, "organization_metadata.json"
        )

    def publish_service_metadata(
        self, service_metadata: ServiceMetadata, storage_type: StorageType = StorageType.IPFS
    ) -> FileURI:
        return self._publish_metadata(service_metadata, storage_type, "service_metadata.json")

    def publish_proto(
        self, proto_dir: Union[str, Path], storage_type: StorageType = StorageType.IPFS
    ) -> FileURI:
        target_dir = Path(proto_dir).resolve()
        if not target_dir.is_dir():
            raise WrongDirectoryError(str(target_dir))

        proto_files = sorted(target_dir.glob("*.proto"))
        if not proto_files:
            raise ProtoFilesNotFoundError(str(target_dir))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_tar_path = Path(temp_dir) / "proto_files.tar.gz"
            with tarfile.open(temp_tar_path, mode="w:gz") as tar:
                for f in proto_files:
                    tar.add(f, arcname=f.name)

            return self._publish_file_in_storage(str(temp_tar_path), storage_type)

    def _publish_metadata(
        self,
        metadata: Union[ServiceMetadata, OrganizationMetadata],
        storage_type: StorageType,
        file_name: str,
    ) -> FileURI:
        json_metadata = metadata.generate_final_json()

        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / file_name
            with open(metadata_path, "w") as f:
                f.write(json_metadata)

            return self._publish_file_in_storage(metadata_path, storage_type)

    def _publish_file_in_storage(
        self, file_path: Union[str, Path], storage_type: StorageType
    ) -> FileURI:
        match storage_type:
            case StorageType.IPFS:
                uri_hash = self._ipfs_client.add(file_path)["Hash"]
            case StorageType.FILECOIN:
                try:
                    uri_hash = self._lighthouse_client.upload(file_path)["data"]["Hash"]
                except Exception as e:
                    raise LighthouseError() from e
            case _:
                raise UnsupportedStorageTypeError(storage_type.value)

        return FileURI(storage_type=storage_type, uri_hash=uri_hash)

    def _get_from_storage(self, uri: FileURI, decode: bool = True) -> Union[bytes, str]:
        match uri.storage_type:
            case StorageType.IPFS:
                file = self._get_from_ipfs_and_checkhash(uri.uri_hash)
            case StorageType.FILECOIN:
                file, _ = self._lighthouse_client.download(uri.uri_hash)
            case _:
                raise UnsupportedStorageTypeError(uri.storage_type.value)
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
                    raise IPFSHashMismatchError()

            except Exception as e:
                raise IPFSHashCheckError() from e

        return data

    @staticmethod
    def _safe_extract_proto(spec_tar: bytes, proto_dir: Union[str, Path]) -> None:
        dest_dir = Path(proto_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(fileobj=io.BytesIO(spec_tar)) as f:
            valid_members = []

            for m in f.getmembers():
                if not m.isfile():
                    raise ExtractingProtoError(
                        f"Security/Format Error: Tarball contains a non-file item: '{m.name}'"
                    )
                if Path(m.name).parent != Path("."):
                    raise ExtractingProtoError(
                        f"Format Error: Tarball contains nested paths ('{m.name}'). Only flat archives are supported."
                    )
                if not m.name.endswith(".proto"):
                    raise ExtractingProtoError(
                        f"Format Error: Unexpected file type '{m.name}'. Only .proto files allowed."
                    )
                target_file = dest_dir / m.name
                if target_file.exists():
                    target_file.unlink()
                    print(f"Removed existing file: {target_file}")
                valid_members.append(m)

            f.extractall(path=dest_dir, members=valid_members, filter="data")
