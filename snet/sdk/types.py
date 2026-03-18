from dataclasses import dataclass
from enum import Enum


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


@dataclass
class ServiceData:
    org_id: str
    service_id: str
    metadata_uri: FileURI
