import importlib
import os
from pathlib import Path
import sys
from typing import Any, NewType
import warnings

import google.protobuf.internal.api_implementation

with warnings.catch_warnings():
    # Suppress the eth-typing package`s warnings related to some new networks
    warnings.filterwarnings("ignore", "Network .* does not have a valid ChainId. eth-typing should be "
                                      "updated with the latest networks.", UserWarning)
    from snet.sdk.metadata_provider.ipfs_metadata_provider import IPFSMetadataProvider

from snet.sdk.payment_strategies.default_payment_strategy import DefaultPaymentStrategy
from snet.cli.commands.sdk_command import SDKCommand
from snet.cli.commands.commands import BlockchainCommand
from snet.cli.config import Config
from snet.cli.utils.utils import bytes32_to_str, type_converter

google.protobuf.internal.api_implementation.Type = lambda: 'python'

from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()
_sym_db.RegisterMessage = lambda x: None


from urllib.parse import urljoin


import web3
from rfc3986 import urlparse
import ipfshttpclient

from snet.sdk.service_client import ServiceClient
from snet.sdk.account import Account
from snet.sdk.mpe.mpe_contract import MPEContract

from snet.contracts import get_contract_object

from snet.cli.metadata.service import mpe_service_metadata_from_json
from snet.cli.utils.ipfs_utils import bytesuri_to_hash, get_from_ipfs_and_checkhash
from snet.cli.utils.utils import find_file_by_keyword

ModuleName = NewType('ModuleName', str)
ServiceStub = NewType('ServiceStub', Any)


class Arguments:
    def __init__(self, org_id=None, service_id=None):
        self.org_id = org_id
        self.service_id = service_id
        self.language = "python"
        self.protodir = Path("~").expanduser().joinpath(".snet")


class SnetSDK:
    """Base Snet SDK"""

    def __init__(self, sdk_config, metadata_provider=None):
        self._sdk_config = sdk_config
        self._metadata_provider = metadata_provider

        # Instantiate Ethereum client
        eth_rpc_endpoint = self._sdk_config.get("eth_rpc_endpoint",
                                                "https://mainnet.infura.io/v3/e7732e1f679e461b9bb4da5653ac3fc2")
        eth_rpc_request_kwargs = self._sdk_config.get("eth_rpc_request_kwargs")

        provider = web3.HTTPProvider(endpoint_uri=eth_rpc_endpoint, request_kwargs=eth_rpc_request_kwargs)

        self.web3 = web3.Web3(provider)

        # Get MPE contract address from config if specified; mostly for local testing
        _mpe_contract_address = self._sdk_config.get("mpe_contract_address", None)
        if _mpe_contract_address is None:
            self.mpe_contract = MPEContract(self.web3)
        else:
            self.mpe_contract = MPEContract(self.web3, _mpe_contract_address)

        # Instantiate IPFS client
        ipfs_endpoint = self._sdk_config.get("default_ipfs_endpoint", "/dns/ipfs.singularitynet.io/tcp/80/")
        self.ipfs_client = ipfshttpclient.connect(ipfs_endpoint)

        # Get Registry contract address from config if specified; mostly for local testing
        _registry_contract_address = self._sdk_config.get("registry_contract_address", None)
        if _registry_contract_address is None:
            self.registry_contract = get_contract_object(self.web3, "Registry")
        else:
            self.registry_contract = get_contract_object(self.web3, "Registry", _registry_contract_address)

        self.account = Account(self.web3, sdk_config, self.mpe_contract)

        global_config = Config(sdk_config=sdk_config)
        self.setup_config(global_config)

    def setup_config(self, config: Config) -> None:
        out_f = sys.stdout
        network = self._sdk_config.get("network", None)
        identity_name = self._sdk_config.get("identity_name", None)
        # Checking for an empty network
        if network and config["session"]["network"] != network:
            config.set_session_network(network, out_f)
        if identity_name:
            self.set_session_identity(identity_name, config, out_f)
        elif len(config.get_all_identities_names()) > 0:
            if "identity" not in config["session"] or config["session"]["identity"] == "":
                raise Exception("identity_name is not passed or selected")

    def set_session_identity(self, identity_name: str, config: Config, out_f):
        if identity_name not in config.get_all_identities_names():
            identity = config.setup_identity()
            config.add_identity(identity_name, identity, out_f)
            config.set_session_identity(identity_name, out_f)
        elif config["session"]["identity"] != identity_name:
            config.set_session_identity(identity_name, out_f)

    def create_service_client(self, org_id: str, service_id: str, group_name=None,
                              payment_channel_management_strategy=None,
                              free_call_auth_token_bin=None,
                              free_call_token_expiry_block=None,
                              options=None,
                              concurrent_calls=1):

        # Create and instance of the Config object, so we can create an instance of SDKCommand
        sdk_config_object = Config(sdk_config=self._sdk_config)
        sdk = SDKCommand(sdk_config_object, args=Arguments(org_id, service_id))

        # Download the proto file and generate stubs if needed
        force_update = self._sdk_config.get('force_update', False)
        if force_update:
            sdk.generate_client_library()
        else:
            path_to_pb_files = self.get_path_to_pb_files(org_id, service_id)
            pb_2_file_name = find_file_by_keyword(path_to_pb_files, keyword="pb2.py")
            pb_2_grpc_file_name = find_file_by_keyword(path_to_pb_files, keyword="pb2_grpc.py")
            if not pb_2_file_name or not pb_2_grpc_file_name:
                sdk.generate_client_library()
        
        if payment_channel_management_strategy is None:
            payment_channel_management_strategy = DefaultPaymentStrategy(concurrent_calls)

        if options is None:
            options = dict()
        options['free_call_auth_token-bin'] = bytes.fromhex(free_call_auth_token_bin) if\
            free_call_token_expiry_block else ""
        options['free-call-token-expiry-block'] = free_call_token_expiry_block if\
            free_call_token_expiry_block else 0
        options['email'] = self._sdk_config.get("email", "")
        options['concurrency'] = self._sdk_config.get("concurrency", True)

        if self._metadata_provider is None:
            self._metadata_provider = IPFSMetadataProvider(self.ipfs_client, self.registry_contract)

        service_metadata = self._metadata_provider.enhance_service_metadata(org_id, service_id)
        group = self._get_service_group_details(service_metadata, group_name)
        strategy = payment_channel_management_strategy
        
        service_stub = self.get_service_stub(org_id, service_id)
        
        pb2_module = self.get_module_by_keyword(org_id, service_id, keyword="pb2.py")
        
        service_client = ServiceClient(org_id, service_id, service_metadata, group, service_stub, strategy,
                                       options, self.mpe_contract, self.account, self.web3, pb2_module)
        return service_client

    def get_service_stub(self, org_id: str, service_id: str) -> ServiceStub:
        path_to_pb_files = self.get_path_to_pb_files(org_id, service_id)
        module_name = self.get_module_by_keyword(org_id, service_id, keyword="pb2_grpc.py")
        package_path = os.path.dirname(path_to_pb_files)
        sys.path.append(package_path)
        try:
            grpc_file = importlib.import_module(module_name)
            properties_and_methods_of_grpc_file = dir(grpc_file)
            class_stub = [elem for elem in properties_and_methods_of_grpc_file if 'Stub' in elem][0]
            service_stub = getattr(grpc_file, class_stub)
            return ServiceStub(service_stub)
        except Exception as e:
            raise Exception(f"Error importing module: {e}")

    def get_path_to_pb_files(self, org_id: str, service_id: str) -> str:
        client_libraries_base_dir_path = Path("~").expanduser().joinpath(".snet")
        path_to_pb_files = f"{client_libraries_base_dir_path}/{org_id}/{service_id}/python/"
        return path_to_pb_files
    
    def get_module_by_keyword(self, org_id: str, service_id: str, keyword: str) -> ModuleName:
        path_to_pb_files = self.get_path_to_pb_files(org_id, service_id)
        file_name = find_file_by_keyword(path_to_pb_files, keyword)
        module_name = os.path.splitext(file_name)[0]
        return ModuleName(module_name)

    def get_service_metadata(self, org_id, service_id):
        (found, registration_id, metadata_uri) = self.registry_contract.functions.getServiceRegistrationById(
            bytes(org_id, "utf-8"),
            bytes(service_id, "utf-8")
        ).call()

        if found is not True:
            raise Exception('No service "{}" found in organization "{}"'.format(service_id, org_id))

        metadata_hash = bytesuri_to_hash(metadata_uri)
        metadata_json = get_from_ipfs_and_checkhash(self.ipfs_client, metadata_hash)
        metadata = mpe_service_metadata_from_json(metadata_json)
        return metadata

    def _get_first_group(self, service_metadata):
        return service_metadata['groups'][0]

    def _get_group_by_group_name(self, service_metadata, group_name):
        for group in service_metadata['groups']:
            if group['group_name'] == group_name:
                return group
        return {}

    def _get_service_group_details(self, service_metadata, group_name):
        if len(service_metadata['groups']) == 0:
            raise Exception("No Groups found for given service, Please add group to the service")

        if group_name is None:
            return self._get_first_group(service_metadata)

        return self._get_group_by_group_name(service_metadata, group_name)

    def get_organization_list(self) -> list:
        global_config = Config(sdk_config=self._sdk_config)
        blockchain_command = BlockchainCommand(config=global_config, args=Arguments())
        org_list = blockchain_command.call_contract_command(
            "Registry", "listOrganizations", [])
        organization_list = []
        for idx, org_id in enumerate(org_list):
            organization_list.append(bytes32_to_str(org_id))
        return organization_list

    def get_services_list(self, org_id: str) -> list:
        global_config = Config(sdk_config=self._sdk_config)
        blockchain_command = BlockchainCommand(config=global_config, args=Arguments())
        (found, org_service_list) = blockchain_command.call_contract_command("Registry",
                                                                             "listServicesForOrganization",
                                                               [type_converter("bytes32")(org_id)])
        if not found:
            raise Exception(f"Organization with id={org_id} doesn't exist!")
        org_service_list = list(map(bytes32_to_str, org_service_list))
        return org_service_list

