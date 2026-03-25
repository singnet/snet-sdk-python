"""
Functions for manipulating service metadata

Metadata format:
----------------------------------------------------
version          - used to track format changes (current version is 1)
display_name     - Display name of the service
encoding         - Service encoding (proto or json)
service_type     - Service type (grpc, jsonrpc or process)
service_description - Service description (arbitrary field)
payment_expiration_threshold - Service will reject payments with expiration less
                                than current_block + payment_expiration_threshold.
                               This field should be used by the client with caution.
                               Client should not accept arbitrary payment_expiration_threshold
model_ipfs_hash  - IPFS HASH to the .tar archive of protobuf service specification
mpe_address      - Address of MultiPartyEscrow contract.
                   Client should use it exclusively for cross-checking of mpe_address,
                        (because service can attack via mpe_address)
                   Daemon can use it directly if authenticity of metadata is confirmed
pricing {}      -  Pricing model
         Possible pricing models:
         1. Fixed price
             price_model   - "fixed_price"
             price_in_cogs -  unique fixed price in cogs for all method (1 FET = 10^18 cogs)
             (other pricing models can be easily supported)
groups []       - group is the number of endpoints which shares same payment channel;
                  grouping strategy is defined by service provider;
                  for example service provider can use region name as group name
     group_name - unique name of the group (human readable)
     group_id   - unique id of the group (random 32 byte string in base64 encoding)
     payment_address - Ethereum address to recieve payments
endpoints[]     - address in the off-chain network to provide a service
     group_name
     endpoint   -  unique endpoint identifier (ip:port)

assets {}       -  asset type and its ipfs value/values
"""

import base64
import secrets

from enum import Enum
from typing import Literal, Any, Optional

from pydantic import BaseModel, Field, model_validator, ValidationInfo

from snet.sdk.exceptions import ServiceMetadataMismatchError
from snet.sdk.registry.models import FileURI
from snet.sdk.registry.organization_metadata import Payment


# Supported Asset types
class AssetType(Enum):
    HERO_IMAGE = "hero_image"
    IMAGES = "images"
    DOCUMENTATION = "documentation"
    TERMS_OF_USE = "terms_of_use"

    @staticmethod
    def is_single_value(asset_type):
        if (
            asset_type == AssetType.HERO_IMAGE.value
            or asset_type == AssetType.DOCUMENTATION.value
            or asset_type == AssetType.TERMS_OF_USE.value
        ):
            return True


def generate_group_id() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


class Pricing(BaseModel):
    price_model: Literal["fixed_price", "method_price"] = Field(default="fixed_price")
    price_in_cogs: int = Field(ge=1, default=1)
    default: bool = Field(default=True)


class Group(BaseModel):
    group_name: str = Field(min_length=1, default="default_group")
    group_id: str = Field(default_factory=generate_group_id, init=False)
    free_calls: int = Field(ge=1, default=3)
    free_call_signer_address: str = Field(default="")
    daemon_addresses: list[str] = Field(default=[])
    endpoints: list[str] = Field(default=[])
    pricing: list[Pricing] = Field(default=[])
    payment: Optional[Payment] = Field(
        default=None
    )  # The field from org metadata for service client functionality


class ServiceDescription(BaseModel):
    url: str = Field(default="")
    short_description: str = Field(default="")
    description: str = Field(default="")


class Media(BaseModel):
    order: int = Field(ge=1, default=1)
    url: str = Field(min_length=1)
    file_type: Literal["image", "video", "archive"]
    alt_text: str = Field(default="")
    asset_type: Literal["hero_image", "proto_file", "demo_component"]


class Contributor(BaseModel):
    name: str = Field(min_length=1)
    email_id: str = Field(default="")


class ServiceMetadata(BaseModel):
    version: int = Field(ge=1, default=1)
    display_name: str = Field(min_length=1)
    encoding: Literal["proto", "json"] = Field(default="proto")
    service_type: Literal["grpc", "http", "jsonrpc"]
    service_api_source: Optional[str] = Field(default=None, init=False)
    model_ipfs_hash: Optional[str] = Field(min_length=1, default=None, init=False, deprecated=True)
    mpe_address: Optional[str] = Field(default=None, init=False)
    groups: list[Group] = Field(default=[])
    service_description: Optional[ServiceDescription] = Field(default=None)
    media: list[Media] = Field(default=[])
    contributors: list[Contributor] = Field(default=[])
    tags: list[str] = Field(default=[])

    @model_validator(mode="before")
    @classmethod
    def restrict_deprecated_fields(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict):
            return data

        is_fetching = info.context and info.context.get("from_storage") is True

        if not is_fetching and data.get("model_ipfs_hash"):
            raise ValueError(
                "The 'model_ipfs_hash' field is deprecated and cannot be used "
                "to create new metadata. Please use 'service_api_source' instead."
            )

        return data

    def generate_final_json(self):
        if self.service_api_source is None:
            if self.model_ipfs_hash is None:
                raise ValueError("The 'service_api_source' field is missing!")
            else:
                self.service_api_source = FileURI.normalize_string_uri(self.model_ipfs_hash)
                self.model_ipfs_hash = None

        if not self.mpe_address:
            raise ServiceMetadataMismatchError("The 'mpe_address' field is missing!")

        if len(self.groups) == 0:
            raise ServiceMetadataMismatchError("There must be one item in 'groups' field at least!")

        if len(self.contributors) == 0:
            raise ServiceMetadataMismatchError(
                "There must be one item in 'contributors' field at least!"
            )

        if not self.service_description:
            raise ServiceMetadataMismatchError("The 'service_description' field is missing!")

        return self.model_dump_json(indent=2, exclude_none=True)
