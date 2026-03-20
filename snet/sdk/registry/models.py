from dataclasses import dataclass
from enum import Enum
from typing import Union

from snet.sdk.utils.utils import bytes32_to_str


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

    @classmethod
    def from_raw_uri(cls, string_uri: Union[str, bytes]) -> "FileURI":
        if not string_uri:
            raise ValueError("'string_uri' cannot be empty!")

        if isinstance(string_uri, bytes):
            string_uri = string_uri.rstrip(b"\0").decode("ascii")

        try:
            s_t_str, u_h = string_uri.split("://")
        except ValueError:
            s_t_str = "ipfs"
            u_h = string_uri

        s_t = StorageType(s_t_str)

        return cls(s_t, u_h)

    def __str__(self) -> str:
        return f"{self.storage_type.value}://{self.uri_hash}"

    @classmethod
    def normalize_string_uri(cls, string_uri: str) -> str:
        return str(FileURI.from_raw_uri(string_uri))


@dataclass
class OrgData:
    org_id: str
    metadata_uri: FileURI
    owner: str
    members: list[str]
    services: list[str]  # IDs

    @classmethod
    def from_raw_data(cls, raw_org_data: RawOrgData) -> "OrgData":
        return cls(
            org_id=bytes32_to_str(raw_org_data.org_id),
            metadata_uri=FileURI.from_raw_uri(raw_org_data.metadata_uri),
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
    def from_raw_data(
        cls, raw_service_data: RawServiceData, org_id: Union[str, bytes]
    ) -> "ServiceData":
        return cls(
            org_id=bytes32_to_str(org_id) if isinstance(org_id, bytes) else org_id,
            service_id=bytes32_to_str(raw_service_data.service_id),
            metadata_uri=FileURI.from_raw_uri(raw_service_data.metadata_uri),
        )
