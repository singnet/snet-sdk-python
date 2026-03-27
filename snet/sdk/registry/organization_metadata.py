import base64
import secrets
from typing import Optional, Literal

from pydantic import BaseModel, Field

from snet.sdk.exceptions import OrganizationMetadataMismatchError


def generate_group_id() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


class Description(BaseModel):
    url: str = Field(default="")
    description: str = Field(min_length=1)
    short_description: str = Field(min_length=1, max_length=160)


class Assets(BaseModel):
    hero_image: str = Field(default="")


class Contact(BaseModel):
    email: str = Field(default="")
    phone: str = Field(default="")
    contact_type: Literal["general", "support"]


class PaymentChannelStorageClient(BaseModel):
    connection_timeout: str = Field(default="5s")
    request_timeout: str = Field(default="5s")
    endpoints: list[str] = Field(min_length=1)


class Payment(BaseModel):
    payment_address: str
    payment_expiration_threshold: int = Field(default=40320)
    payment_channel_storage_type: Literal["etcd"] = Field(default="etcd")
    payment_channel_storage_client: PaymentChannelStorageClient


class Group(BaseModel):
    group_name: str
    group_id: str = Field(default_factory=generate_group_id)
    payment: Payment


class OrganizationMetadata(BaseModel):
    org_name: str = Field(min_length=1)
    org_id: Optional[str] = Field(default=None, init=False)
    org_type: Literal["organization", "individual"]
    description: Optional[Description] = Field(default=None)
    assets: Optional[Assets] = Field(default=None)
    contacts: list[Contact] = Field(default_factory=list)
    groups: list[Group] = Field(default_factory=list)

    def add_group(
        self,
        payment_address: str,
        payment_channel_storage_client_endpoints: list[str],
        group_name: str = "default_group",
        payment_expiration_threshold: int = 40320,
        payment_channel_storage_client_connection_timeout: str = "5s",
        payment_channel_storage_client_request_timeout: str = "5s",
    ) -> "OrganizationMetadata":
        existing_org_groups = [g.group_name for g in self.groups]
        if group_name in existing_org_groups:
            raise OrganizationMetadataMismatchError(
                f"Group with group_name {group_name} already exists!"
            )

        self.groups.append(
            Group(
                group_name=group_name,
                payment=Payment(
                    payment_address=payment_address,
                    payment_expiration_threshold=payment_expiration_threshold,
                    payment_channel_storage_client=PaymentChannelStorageClient(
                        connection_timeout=payment_channel_storage_client_connection_timeout,
                        request_timeout=payment_channel_storage_client_request_timeout,
                        endpoints=payment_channel_storage_client_endpoints,
                    ),
                ),
            )
        )

        return self

    def add_contact(
        self,
        email: str = "",
        phone: str = "",
        contact_type: Literal["general", "support"] = "support",
    ) -> "OrganizationMetadata":
        self.contacts.append(Contact(email=email, phone=phone, contact_type=contact_type))

        return self

    def add_description(
        self, description: str, short_description: str, url: str = ""
    ) -> "OrganizationMetadata":
        self.description = Description(
            url=url, description=description, short_description=short_description
        )

        return self

    def add_assets(self, hero_image: str) -> "OrganizationMetadata":
        self.assets = Assets(hero_image=hero_image)
        return self

    def generate_final_json(self):
        if not self.org_id:
            raise OrganizationMetadataMismatchError("The 'org_id' field is missing!")

        if not self.description:
            raise OrganizationMetadataMismatchError("The 'description' field is missing!")

        if not self.assets:
            raise OrganizationMetadataMismatchError("The 'assets' field is missing!")

        if not self.contacts:
            raise OrganizationMetadataMismatchError("The 'contacts' field is missing!")

        if len(self.groups) == 0:
            raise OrganizationMetadataMismatchError(
                "There must be one item in 'groups' field at least!"
            )

        return self.model_dump_json(indent=2, exclude_none=True)

    def validate_metadata(self) -> tuple[bool, str]:
        try:
            self.generate_final_json()
        except OrganizationMetadataMismatchError as e:
            return False, str(e)

        return True, ""
