import base64
import importlib
import re
import os
from pathlib import Path
from typing import Any

from eth_typing import BlockNumber
import grpc
from hexbytes import HexBytes
import web3
from eth_account.messages import defunct_hash_message
from rfc3986 import urlparse

from snet.sdk import generic_client_interceptor, FreeCallPaymentStrategy
from snet.sdk.account import Account
from snet.sdk.mpe.mpe_contract import MPEContract
from snet.sdk.mpe.payment_channel import PaymentChannel
from snet.sdk.mpe.payment_channel_provider import PaymentChannelProvider
from snet.sdk.payment_strategies.prepaid_payment_strategy import PrePaidPaymentStrategy
from snet.sdk.resources.root_certificate import certificate
from snet.sdk.storage_provider.service_metadata import MPEServiceMetadata
from snet.sdk.custom_typing import ModuleName, ServiceStub
from snet.sdk.utils.utils import (RESOURCES_PATH, add_to_path,
                                  find_file_by_keyword)
from snet.sdk.training.training import Training
from snet.sdk.training.exceptions import NoTrainingException
from snet.sdk.utils.call_utils import create_intercept_call_func


class ServiceClient:
    def __init__(
        self,
        org_id: str,
        service_id: str,
        service_metadata: MPEServiceMetadata,
        group: dict,
        service_stubs: list[ServiceStub],
        payment_strategy,
        options: dict,
        mpe_contract: MPEContract,
        account: Account,
        sdk_web3: web3.Web3,
        pb2_module: ModuleName,
        payment_channel_provider: PaymentChannelProvider,
        path_to_pb_files: Path,
        training_added: bool = False
    ):
        self.org_id = org_id
        self.service_id = service_id
        self.service_metadata = service_metadata
        self.group = group
        self.payment_strategy = payment_strategy
        if isinstance(payment_strategy, PrePaidPaymentStrategy):
            self.payment_strategy.set_concurrent_calls(options["concurrent_calls"])
        self.options = options
        self.mpe_address = mpe_contract.contract.address
        self.account = account
        self.sdk_web3 = sdk_web3
        self.pb2_module = (importlib.import_module(pb2_module)
                                if isinstance(pb2_module, str)
                                else pb2_module)
        self.payment_channel_provider = payment_channel_provider
        self.path_to_pb_files = path_to_pb_files

        self.expiry_threshold: int = self.group["payment"]["payment_expiration_threshold"]
        self.__base_grpc_channel = self._get_grpc_channel()
        _intercept_call_func = create_intercept_call_func(self.payment_strategy.get_payment_metadata, self)
        self.grpc_channel = grpc.intercept_channel(
            self.__base_grpc_channel,
            generic_client_interceptor.create(_intercept_call_func)
        )
        self.service_stubs = service_stubs
        self.payment_channel_state_service_client = self._generate_payment_channel_state_service_client()
        self.payment_channels = []
        self.last_read_block: int = 0
        self.__training = Training(self, training_added)

    def call_rpc(self, rpc_name: str, message_class: str, **kwargs) -> Any:
        service = self._get_service_stub(rpc_name)
        if "model_id" in kwargs:
            kwargs["model_id"] = self._get_training_model_id(kwargs["model_id"])
        rpc_method = getattr(service, rpc_name)
        request = getattr(self.pb2_module, message_class)(**kwargs)
        return rpc_method(request)

    def _get_payment_expiration_threshold_for_group(self):
        pass

    def _get_service_stub(self, rpc_name: str) -> Any:
        for service_stub in self.service_stubs:
            grpc_stub = self._generate_grpc_stub(service_stub)
            if hasattr(grpc_stub, rpc_name):
                return grpc_stub
        raise Exception(f"Service stub for {rpc_name} not found")

    def _generate_grpc_stub(self, service_stub: ServiceStub) -> Any:
        grpc_channel = self.__base_grpc_channel
        disable_blockchain_operations: bool = self.options.get(
            "disable_blockchain_operations",
            False
        )
        if not disable_blockchain_operations:
            grpc_channel = self.grpc_channel
        stub_instance = service_stub(grpc_channel)
        return stub_instance

    def get_grpc_base_channel(self) -> grpc.Channel:
        return self.__base_grpc_channel

    def _get_grpc_channel(self) -> grpc.Channel:
        endpoint = self.options.get("endpoint", None)
        if endpoint is None:
            endpoint = self.service_metadata.get_all_endpoints_for_group(self.group["group_name"])[0]
        endpoint_object = urlparse(endpoint)
        if endpoint_object.port is not None:
            channel_endpoint = endpoint_object.hostname + ":" + str(endpoint_object.port)
        else:
            channel_endpoint = endpoint_object.hostname

        if endpoint_object.scheme == "http":
            return grpc.insecure_channel(channel_endpoint)
        elif endpoint_object.scheme == "https":
            return grpc.secure_channel(channel_endpoint,
                                       grpc.ssl_channel_credentials(root_certificates=certificate))
        else:
            raise ValueError('Unsupported scheme in service metadata ("{}")'.format(endpoint_object.scheme))

    def _filter_existing_channels_from_new_payment_channels(
        self,
        new_payment_channels: list[PaymentChannel]
    ) -> list[PaymentChannel]:
        new_channels_to_be_added = []

        # need to change this logic ,use maps to manage channels so that we can easily navigate it
        for new_payment_channel in new_payment_channels:
            existing_channel = False
            for existing_payment_channel in self.payment_channels:
                if new_payment_channel.channel_id == existing_payment_channel.channel_id:
                    existing_channel = True
                    break

            if not existing_channel:
                new_channels_to_be_added.append(new_payment_channel)

        return new_channels_to_be_added

    def load_open_channels(self) -> list[PaymentChannel]:
        current_block_number = self.sdk_web3.eth.block_number
        payment_address = self.group["payment"]["payment_address"]
        group_id = base64.b64decode(str(self.group["group_id"]))
        new_payment_channels = (
            self.payment_channel_provider.get_past_open_channels(
                self.account, payment_address,
                group_id, self.payment_channel_state_service_client
            )
        )
        filter_new_channels = self._filter_existing_channels_from_new_payment_channels(new_payment_channels)
        self.payment_channels = (self.payment_channels + filter_new_channels)
        self.last_read_block = current_block_number
        return self.payment_channels

    def get_current_block_number(self) -> BlockNumber:
        return self.sdk_web3.eth.block_number

    def update_channel_states(self) -> list[PaymentChannel]:
        for channel in self.payment_channels:
            channel.sync_state()
        return self.payment_channels

    def default_channel_expiration(self) -> int:
        current_block_number = self.sdk_web3.eth.get_block("latest").number
        return current_block_number + self.expiry_threshold

    def _generate_payment_channel_state_service_client(self) -> Any:
        grpc_channel = self.__base_grpc_channel
        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service = importlib.import_module("state_service_pb2_grpc")
        return state_service.PaymentChannelStateServiceStub(grpc_channel)

    def open_channel(self, amount: int, expiration: int) -> PaymentChannel:
        payment_address = self.group["payment"]["payment_address"]
        group_id = base64.b64decode(str(self.group["group_id"]))
        return self.payment_channel_provider.open_channel(
            self.account, amount, expiration, payment_address,
            group_id, self.payment_channel_state_service_client
        )

    def deposit_and_open_channel(self, amount: int,
                                 expiration: int) -> PaymentChannel:
        payment_address = self.group["payment"]["payment_address"]
        group_id = base64.b64decode(str(self.group["group_id"]))
        return self.payment_channel_provider.deposit_and_open_channel(
            self.account, amount, expiration, payment_address,
            group_id, self.payment_channel_state_service_client
        )

    def get_price(self) -> int:
        return self.group["pricing"][0]["price_in_cogs"]

    def generate_signature(self, message: bytes) -> bytes:
        return bytes(self.sdk_web3.eth.account._sign_hash(
            defunct_hash_message(message), self.account.signer_private_key
        ).signature)

    def generate_training_signature(self, text: str, address: str,
                                    block_number: BlockNumber) -> HexBytes:
        address = web3.Web3.to_checksum_address(address)
        message = web3.Web3.solidity_keccak(
            ["string", "address", "uint256"],
            [text, address, block_number]
        )
        return self.sdk_web3.eth.account._sign_hash(
            defunct_hash_message(message), self.account.signer_private_key
        ).signature

    def get_service_details(self) -> tuple[str, str, str, str]:
        return (self.org_id,
                self.service_id,
                self.group["group_id"],
                self.service_metadata.get_all_endpoints_for_group(
                    self.group["group_name"]
                )[0])

    @property
    def training(self) -> Training:
        if not self.__training.is_enabled:
            raise NoTrainingException(self.org_id, self.service_id)
        return self.__training

    def _get_training_model_id(self, model_id: str) -> Any:
        return self.training.get_model_id_object(model_id)

    def get_concurrency_flag(self) -> bool:
        return self.options.get('concurrency', True)

    def get_concurrency_token_and_channel(self) -> tuple[str, PaymentChannel]:
        return self.payment_strategy.get_concurrency_token_and_channel(self)

    def get_concurrent_calls(self):
        return self.options.get('concurrent_calls', 1)

    def set_concurrency_token_and_channel(self, token: str,
                                          channel: PaymentChannel) -> None:
        self.payment_strategy.concurrency_token = token
        self.payment_strategy.channel = channel

    def get_services_and_messages_info(self) -> tuple[dict, dict]:
        # Get proto file filepath and open it
        proto_file_name = find_file_by_keyword(directory=self.path_to_pb_files,
                                               keyword=".proto", exclude=["training"])
        proto_filepath = os.path.join(self.path_to_pb_files, proto_file_name)
        with open(proto_filepath, 'r') as file:
            proto_content = file.read()
        # Regular expression patterns to match services, methods,
        # messages and fields
        service_pattern = re.compile(r'service\s+(\w+)\s*{')
        rpc_pattern = re.compile(
            r'rpc\s+(\w+)\s*\((\w+)\)\s+returns\s+\((\w+)\)'
        )
        message_pattern = re.compile(r'message\s+(\w+)\s*{')
        field_pattern = re.compile(r'\s*(\w+)\s+(\w+)\s*=\s*\d+\s*;')

        services = {}
        messages = {}
        current_service = None
        current_message = None

        for line in proto_content.splitlines():
            # Match a service definition
            service_match = service_pattern.search(line)
            if service_match:
                current_service = service_match.group(1)
                services[current_service] = []
                continue

            # Match an RPC method inside a service
            if current_service:
                rpc_match = rpc_pattern.search(line)
                if rpc_match:
                    method_name = rpc_match.group(1)
                    input_type = rpc_match.group(2)
                    output_type = rpc_match.group(3)
                    services[current_service].append((method_name, input_type,
                                                      output_type))

            # Match a message definition
            message_match = message_pattern.search(line)
            if message_match:
                current_message = message_match.group(1)
                messages[current_message] = []
                continue

            # Match a field inside a message
            if current_message:
                field_match = field_pattern.search(line)
                if field_match:
                    field_type = field_match.group(1)
                    field_name = field_match.group(2)
                    messages[current_message].append((field_type, field_name))

        return services, messages

    def get_services_and_messages_info_as_pretty_string(self) -> str:
        services, messages = self.get_services_and_messages_info()

        string_output = ""
        # Prettify the parsed services and their methods
        for service, methods in services.items():
            string_output += f"Service: {service}\n"
            for method_name, input_type, output_type in methods:
                string_output += (f"  Method: {method_name},"
                                  f" Input: {input_type},"
                                  f" Output: {output_type}\n")

        # Prettify the messages and their fields
        for message, fields in messages.items():
            string_output += f"Message: {message}\n"
            for field_type, field_name in fields:
                string_output += f"  Field: {field_type} {field_name}\n"
        return string_output

    def get_free_calls_available(self) -> int:
        payment_strategy = self.payment_strategy
        if not isinstance(payment_strategy, FreeCallPaymentStrategy):
            payment_strategy = FreeCallPaymentStrategy()

        return payment_strategy.get_free_calls_available(self)
