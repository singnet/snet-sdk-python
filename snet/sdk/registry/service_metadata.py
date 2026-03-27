from typing import Literal, Optional

from pydantic import BaseModel, Field

from snet.sdk.exceptions import ServiceMetadataMismatchError
from snet.sdk.registry.models import FileURI
from snet.sdk.registry.organization_metadata import Payment, generate_group_id


class Pricing(BaseModel):
    price_model: Literal["fixed_price", "method_price"]
    price_in_cogs: int = Field(ge=1)
    default: bool = Field(default=True)


class Group(BaseModel):
    group_name: str = Field(min_length=1, default="default_group")
    group_id: str = Field(default_factory=generate_group_id, init=False)
    free_calls: int = Field(ge=1, default=3)
    free_call_signer_address: str
    daemon_addresses: list[str] = Field(default_factory=list)
    endpoints: list[str]
    pricing: list[Pricing]
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
    groups: list[Group] = Field(default_factory=list)
    service_description: ServiceDescription = Field(default_factory=ServiceDescription)
    media: list[Media] = Field(default_factory=list)
    contributors: list[Contributor] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    def add_group(
        self,
        free_call_signer_address: str,
        endpoints: list[str],
        group_name: str = "default_group",
        free_calls_amount: int = 3,
        daemon_addresses: Optional[list[str]] = None,
        price_model: Literal["fixed_price", "method_price"] = "fixed_price",
        price_in_cogs: int = 1,
        default: bool = True,
    ) -> "ServiceMetadata":
        existing_group_names = [g.group_name for g in self.groups]
        if group_name in existing_group_names:
            raise ServiceMetadataMismatchError(
                f"Group with group_name {group_name} already exists!"
            )
        if daemon_addresses is None:
            daemon_addresses = []
        self.groups.append(
            Group(
                group_name=group_name,
                free_calls=free_calls_amount,
                free_call_signer_address=free_call_signer_address,
                daemon_addresses=daemon_addresses,
                endpoints=endpoints,
                pricing=Pricing(
                    price_model=price_model, price_in_cogs=price_in_cogs, default=default
                ),
            )
        )

        return self

    def add_description(
        self,
        url: Optional[str] = None,
        short_description: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "ServiceMetadata":
        for key, value in locals().items():
            if value is not None:
                setattr(self.service_description, key, value)

        return self

    def add_media(
        self,
        url: str,
        file_type: Literal["image", "video", "archive"],
        asset_type: Literal["hero_image", "proto_file", "demo_component"],
        alt_text: str = "",
    ) -> "ServiceMetadata":
        orders = [m.order for m in self.media]
        if orders:
            order = max(orders) + 1
        else:
            order = 1

        self.media.append(
            Media(
                order=order, url=url, file_type=file_type, asset_type=asset_type, alt_text=alt_text
            )
        )

        return self

    def add_contributor(self, name: str, email: str = "") -> "ServiceMetadata":
        self.contributors.append(Contributor(name=name, email_id=email))

        return self

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

    def validate_metadata(self) -> tuple[bool, str]:
        try:
            self.generate_final_json()
        except ServiceMetadataMismatchError as e:
            return False, str(e)

        return True, ""
