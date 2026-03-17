from dataclasses import dataclass
from enum import Enum
from typing import Union

from snet.sdk.utils.utils import bytes32_to_str, bytesuri_to_hash


@dataclass
class RawOrgData:
    org_id: bytes
    metadata_uri: bytes
    owner: str
    members: list[str]
    services: list[bytes]  # IDs


@dataclass
class RawServiceData:
    service_id: bytes
    metadata_uri: bytes


class StorageType(Enum):
    IPFS = "ipfs"
    FILECOIN = "filecoin"


@dataclass
class FileURI:
    storage_type: StorageType
    uri_hash: str


@dataclass
class OrgData:
    org_id: str
    metadata_uri: FileURI
    owner: str
    members: list[str]
    services: list[str]  # IDs

    @classmethod
    def from_raw_org_data(cls, raw_org_data: RawOrgData):
        return OrgData(
            org_id=bytes32_to_str(raw_org_data.org_id),
            metadata_uri=bytesuri_to_hash(raw_org_data.metadata_uri),
            owner=raw_org_data.owner,
            members=raw_org_data.members,
            services=list(map(bytes32_to_str, raw_org_data.services)),
        )


@dataclass
class ServiceData:
    org_id: str
    service_id: str
    metadata_uri: FileURI

    @classmethod
    def from_raw_service_data(cls, raw_service_data: RawServiceData, org_id: Union[str, bytes]):
        return ServiceData(
            org_id=bytes32_to_str(org_id) if isinstance(org_id, bytes) else org_id,
            service_id=bytes32_to_str(raw_service_data.service_id),
            metadata_uri=bytesuri_to_hash(raw_service_data.metadata_uri),
        )
