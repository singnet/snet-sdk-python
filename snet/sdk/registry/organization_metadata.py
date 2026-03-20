from typing import Optional, Literal

from pydantic import BaseModel, Field


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
    endpoints: list[str] = Field(default=[])


class Payment(BaseModel):
    payment_address: str
    payment_expiration_threshold: int = Field(default=40320)
    payment_channel_storage_type: Literal["etcd"] = Field(default="etcd")
    payment_channel_storage_client: Optional[PaymentChannelStorageClient] = Field(default=None)


class Group(BaseModel):
    group_name: str
    group_id: str
    payment: Payment


class OrganizationMetadata(BaseModel):
    org_name: str = Field(min_length=1)
    org_id: Optional[str] = Field(default=None, init=False)
    org_type: Literal["organization", "individual"]
    description: Optional[Description] = Field(default=None)
    assets: Optional[Assets] = Field(default=None)
    contacts: list[Contact] = Field(default=[])
    groups: list[Group] = Field(default=[])

    def generate_final_json(self):
        if not self.org_id:
            raise ValueError("The 'org_id' field is missing!")

        if not self.description:
            raise ValueError("The 'description' field is missing!")

        if not self.assets:
            raise ValueError("The 'assets' field is missing!")

        if not self.contacts:
            raise ValueError("The 'contacts' field is missing!")

        if len(self.groups) == 0:
            raise ValueError("There must be one item in 'groups' field at least!")

        return self.model_dump_json(indent=2, exclude_none=True)
