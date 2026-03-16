from typing import Union

from snet.contracts import get_contract_object

from snet.sdk.account import Account
from snet.sdk.config import config
from snet.sdk.utils.utils import type_converter, bytes32_to_str, get_we3_object


class RegistryContract:
    def __init__(self):
        self.w3 = get_we3_object()
        self.contract = get_contract_object(self.w3, "Registry", config.REGISTRY_CONTRACT_ADDRESS)

    # READ METHODS

    def get_org(self, org_id: str):
        found, _, org_metadata_uri, owner, members, service_ids = (
            self.contract.functions.getOrganizationById(type_converter("bytes32")(org_id)).call()
        )
        if not found:
            # TODO: configure exceptions
            raise Exception()

        # TODO: new type
        return org_metadata_uri, owner, members, service_ids

    def get_service(self, org_id: str, service_id: str) -> bytes:
        found, _, service_metadata_uri = self.contract.functions.getServiceRegistrationById(
            type_converter("bytes32")(org_id), type_converter("bytes32")(service_id)
        ).call()
        if not found:
            # TODO: configure exceptions
            raise Exception()

        return service_metadata_uri

    def list_orgs(self):
        org_list = self.contract.functions.listOrganizations().call()
        return list(map(bytes32_to_str, org_list))

    def list_service_for_org(self, org_id: str):
        found, org_service_list = self.contract.functions.listServicesForOrganization(
            type_converter("bytes32")(org_id)
        ).call()
        if not found:
            # TODO: configure exceptions
            raise Exception()
        else:
            return list(map(bytes32_to_str, org_service_list))

    # WRITE METHODS

    def add_org_members(
        self, account: Account, org_id: str, members: Union[str, list[str], None]
    ): ...

    def update_org_metadata(self, account: Account, org_id: str, metadata_uri: str): ...

    def change_org_owner(self, account: Account, org_id: str, new_owner: str): ...

    def create_org(
        self, account: Account, org_id: str, metadata_uri: str, members: Union[str, list[str], None]
    ): ...

    def create_service(self, account: Account, org_id: str, service_id: str, metadata_uri: str): ...

    def delete_org(self, account: Account, org_id: str): ...

    def delete_service(self, account: Account, org_id: str, service_id: str): ...

    def remove_org_members(
        self, account: Account, org_id: str, members_to_remove: Union[str, list[str]]
    ): ...

    def update_service_metadata(
        self, account: Account, org_id: str, service_id: str, metadata_uri: str
    ): ...
