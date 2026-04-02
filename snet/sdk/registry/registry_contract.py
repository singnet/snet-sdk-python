from typing import Optional

from eth_utils import is_checksum_address
from snet.contracts import get_contract_object
from web3.types import TxReceipt

from snet.sdk.account import Account
from snet.sdk.config import config
from snet.sdk.exceptions import (
    OrganizationNotFoundError,
    ServiceNotFoundError,
    UnauthorizedOrgMemberError,
    UnauthorizedOrgOwnerError,
    IncorrectWalletAddressError,
)
from snet.sdk.registry.models import RawOrgData, OrgData, ServiceData, RawServiceData, FileURI
from snet.sdk.utils.utils import (
    type_converter,
    bytes32_to_str,
    get_we3_object,
)


class RegistryContract:
    def __init__(self):
        self.w3 = get_we3_object()
        self.contract = get_contract_object(self.w3, "Registry", config.REGISTRY_CONTRACT_ADDRESS)

    # READ METHODS

    def get_org(self, org_id: str) -> OrgData:
        found, found_org_id, org_metadata_uri, owner, members, service_ids = (
            self.contract.functions.getOrganizationById(type_converter("bytes32")(org_id)).call()
        )
        if not found:
            raise OrganizationNotFoundError(org_id)

        return OrgData.from_raw_data(
            RawOrgData(
                org_id=found_org_id,
                metadata_uri=org_metadata_uri,
                owner=owner,
                members=members,
                services=service_ids,
            )
        )

    def get_service(self, org_id: str, service_id: str) -> ServiceData:
        found, found_service_id, service_metadata_uri = (
            self.contract.functions.getServiceRegistrationById(
                type_converter("bytes32")(org_id), type_converter("bytes32")(service_id)
            ).call()
        )
        if not found:
            raise ServiceNotFoundError(org_id, service_id)

        return ServiceData.from_raw_data(
            RawServiceData(service_id=found_service_id, metadata_uri=service_metadata_uri),
            org_id=org_id,
        )

    def list_orgs(self) -> list[str]:
        org_list = self.contract.functions.listOrganizations().call()
        return list(map(bytes32_to_str, org_list))

    def list_service_for_org(self, org_id: str) -> list[str]:
        found, org_service_list = self.contract.functions.listServicesForOrganization(
            type_converter("bytes32")(org_id)
        ).call()
        if not found:
            raise OrganizationNotFoundError(org_id)
        else:
            return list(map(bytes32_to_str, org_service_list))

    # WRITE METHODS

    def add_org_members(self, account: Account, org_id: str, new_members: list[str]) -> TxReceipt:
        org = self.get_org(org_id)

        if account.address != org.owner:
            raise UnauthorizedOrgOwnerError(org_id, account.address)

        for member in new_members:
            if not is_checksum_address(member):
                raise IncorrectWalletAddressError(member)

        return account.send_transaction(
            self.contract.functions.addOrganizationMembers,
            type_converter("bytes32")(org_id),
            new_members,
        )

    def update_org_metadata(
        self, account: Account, org_id: str, metadata_uri: FileURI
    ) -> TxReceipt:
        org = self.get_org(org_id)

        if account.address != org.owner:
            raise UnauthorizedOrgOwnerError(org_id, account.address)

        return account.send_transaction(
            self.contract.functions.changeOrganizationMetadataURI,
            type_converter("bytes32")(org_id),
            metadata_uri.to_bytes_uri(),
        )

    def change_org_owner(self, account: Account, org_id: str, new_owner: str) -> TxReceipt:
        org = self.get_org(org_id)

        if account.address != org.owner:
            raise UnauthorizedOrgOwnerError(org_id, account.address)

        if not is_checksum_address(new_owner):
            raise IncorrectWalletAddressError(new_owner)

        return account.send_transaction(
            self.contract.functions.changeOrganizationOwner,
            type_converter("bytes32")(org_id),
            new_owner,
        )

    def create_org(
        self,
        account: Account,
        org_id: str,
        metadata_uri: FileURI,
        members: Optional[list[str]] = None,
    ) -> TxReceipt:
        if members is None:
            members = []

        return account.send_transaction(
            self.contract.functions.createOrganization,
            type_converter("bytes32")(org_id),
            metadata_uri.to_bytes_uri(),
            members,
        )

    def create_service(
        self, account: Account, org_id: str, service_id: str, metadata_uri: FileURI
    ) -> TxReceipt:
        org = self.get_org(org_id)

        if account.address not in org.members:
            raise UnauthorizedOrgMemberError(org_id, account.address)

        return account.send_transaction(
            self.contract.functions.createServiceRegistration,
            type_converter("bytes32")(org_id),
            type_converter("bytes32")(service_id),
            metadata_uri.to_bytes_uri(),
        )

    def delete_org(self, account: Account, org_id: str) -> TxReceipt:
        org = self.get_org(org_id)

        if account.address != org.owner:
            raise UnauthorizedOrgOwnerError(org_id, account.address)

        return account.send_transaction(
            self.contract.functions.deleteOrganization, type_converter("bytes32")(org_id)
        )

    def delete_service(self, account: Account, org_id: str, service_id: str):
        org = self.get_org(org_id)
        if account.address not in org.members:
            raise UnauthorizedOrgMemberError(org_id, account.address)

        self.get_service(org_id, service_id)  # to check if the service exists

        return account.send_transaction(
            self.contract.functions.deleteServiceRegistration,
            type_converter("bytes32")(org_id),
            type_converter("bytes32")(service_id),
        )

    def remove_org_members(
        self, account: Account, org_id: str, members_to_remove: list[str]
    ) -> TxReceipt:
        org = self.get_org(org_id)

        if account.address != org.owner:
            raise UnauthorizedOrgOwnerError(org_id, account.address)

        return account.send_transaction(
            self.contract.functions.removeOrganizationMembers,
            type_converter("bytes32")(org_id),
            members_to_remove,
        )

    def update_service_metadata(
        self, account: Account, org_id: str, service_id: str, metadata_uri: FileURI
    ) -> TxReceipt:
        org = self.get_org(org_id)
        if account.address not in org.members:
            raise UnauthorizedOrgMemberError(org_id, account.address)

        self.get_service(org_id, service_id)  # to check if the service exists

        return account.send_transaction(
            self.contract.functions.updateServiceRegistration,
            type_converter("bytes32")(org_id),
            type_converter("bytes32")(service_id),
            metadata_uri.to_bytes_uri(),
        )
