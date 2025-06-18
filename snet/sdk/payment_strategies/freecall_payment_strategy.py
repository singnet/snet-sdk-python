import importlib

import grpc
import web3

from snet.sdk.payment_strategies.payment_strategy import PaymentStrategy
from snet.sdk.utils.utils import RESOURCES_PATH, add_to_path

class FreeCallPaymentStrategy(PaymentStrategy):

    def __init__(self):
        self._user_address = None
        self._free_call_token = None
        self._token_expiration_block = None

    def get_free_calls_available(self, service_client) -> int:
        if not self._user_address:
            self._user_address = service_client.account.signer_address

        current_block_number = service_client.get_current_block_number()

        if (not self._free_call_token or
                not self._token_expiration_block or
                current_block_number > self._token_expiration_block):
            self._free_call_token, self._token_expiration_block = self.get_free_call_token_details(service_client)

        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2 = importlib.import_module("state_service_pb2")

        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")

        signature, _ = self.generate_signature(service_client, current_block_number)
        request = state_service_pb2.FreeCallStateRequest(
            address=self._user_address,
            free_call_token=self._free_call_token,
            signature=signature,
            current_block=current_block_number
        )

        channel = service_client.get_grpc_base_channel()
        stub = state_service_pb2_grpc.FreeCallStateServiceStub(channel)

        try:
            response = stub.GetFreeCallsAvailable(request)
            return response.free_calls_available
        except grpc.RpcError as e:
            if self._user_address:
                print(f"Warning: {e.details()}")
            return 0

    def get_payment_metadata(self, service_client) -> list:
        if self.get_free_calls_available(service_client) <= 0:
            raise Exception(f"Free calls limit for address {self._user_address} has expired. Please use another payment strategy")
        signature, current_block_number = self.generate_signature(service_client)
        metadata = [("snet-free-call-auth-token-bin", self._free_call_token),
                    ("snet-payment-type", "free-call"),
                    ("snet-free-call-user-address", self._user_address),
                    ("snet-current-block-number", str(current_block_number)),
                    ("snet-payment-channel-signature-bin", signature)]

        return metadata

    def generate_signature(self, service_client, current_block_number=None, with_token=True) -> tuple[bytes, int]:
        if not current_block_number:
            current_block_number = service_client.get_current_block_number()
        org_id, service_id, group_id, _ = service_client.get_service_details()

        message_types = ["string", "string", "string", "string", "string", "uint256", "bytes32"]
        message_values = ["__prefix_free_trial", self._user_address, org_id, service_id, group_id,
                          current_block_number, self._free_call_token]

        if not with_token:
            message_types = message_types[:-1]
            message_values = message_values[:-1]

        message = web3.Web3.solidity_keccak(message_types, message_values)
        return service_client.generate_signature(message), current_block_number

    def get_free_call_token_details(self, service_client, current_block_number=None) -> tuple[bytes, int]:

        signature, current_block_number = self.generate_signature(service_client, current_block_number, with_token=False)

        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2 = importlib.import_module("state_service_pb2")

        request = state_service_pb2.GetFreeCallTokenRequest(
            address=self._user_address,
            signature=signature,
            current_block=current_block_number
        )

        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")

        channel = service_client.get_grpc_base_channel()
        stub = state_service_pb2_grpc.FreeCallStateServiceStub(channel)
        response = stub.GetFreeCallToken(request)

        return response.token, response.token_expiration_block
        