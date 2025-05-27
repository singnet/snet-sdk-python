import importlib
from urllib.parse import urlparse

import grpc
from grpc import _channel
import web3

from snet.sdk.payment_strategies.payment_strategy import PaymentStrategy
from snet.sdk.resources.root_certificate import certificate
from snet.sdk.utils.utils import RESOURCES_PATH, add_to_path

class FreeCallPaymentStrategy(PaymentStrategy):

    def is_free_call_available(self, service_client) -> bool:
        try:
            self._user_address = service_client.account.signer_address
            self._free_call_token, self._token_expiry_date_block = self.get_free_call_token_details(service_client)

            if not self._free_call_token:
                return False

            with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
                state_service_pb2 = importlib.import_module("state_service_pb2")

            with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
                state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")

            signature, current_block_number = self.generate_signature(service_client)

            request = state_service_pb2.FreeCallStateRequest()
            request.user_address = self._user_address
            request.token_for_free_call = self._free_call_token
            request.token_expiry_date_block = self._token_expiry_date_block
            request.signature = signature
            request.current_block = current_block_number

            channel = self.select_channel(service_client)

            stub = state_service_pb2_grpc.FreeCallStateServiceStub(channel)
            response = stub.GetFreeCallsAvailable(request)
            if response.free_calls_available > 0:
                return True
            return False
        except grpc.RpcError as e:
            if self._user_address:
                print(f"Warning: {e.details()}")
            return False
        except Exception as e:
            return False

    def get_payment_metadata(self, service_client) -> list:
        signature, current_block_number = self.generate_signature(service_client)
        metadata = [("snet-free-call-auth-token-bin", self._free_call_token),
                    ("snet-payment-type", "free-call"),
                    ("snet-free-call-user-address", self._user_address),
                    ("snet-current-block-number", str(current_block_number)),
                    ("snet-payment-channel-signature-bin", signature)]

        return metadata

    def select_channel(self, service_client) -> _channel.Channel:
        _, _, _, daemon_endpoint = service_client.get_service_details()
        endpoint_object = urlparse(daemon_endpoint)
        if endpoint_object.port is not None:
            channel_endpoint = endpoint_object.hostname + ":" + str(endpoint_object.port)
        else:
            channel_endpoint = endpoint_object.hostname

        if endpoint_object.scheme == "http":
            channel = grpc.insecure_channel(channel_endpoint)
        elif endpoint_object.scheme == "https":
            channel = grpc.secure_channel(channel_endpoint, grpc.ssl_channel_credentials(root_certificates=certificate))
        else:
            raise ValueError('Unsupported scheme in service metadata ("{}")'.format(endpoint_object.scheme))
        return channel

    def generate_signature(self, service_client) -> tuple[bytes, int]:
        org_id, service_id, group_id, _ = service_client.get_service_details()

        if self._token_expiry_date_block == 0 or len(self._user_address) == 0 or len(self._free_call_token) == 0:
            raise Exception(
                "You are using default 'FreeCallPaymentStrategy' to use this strategy you need to pass "
                "'free_call_auth_token-bin','user_address','free-call-token-expiry-block' in config")

        current_block_number = service_client.get_current_block_number()

        message = web3.Web3.solidity_keccak(
            ["string", "string", "string", "string", "string", "uint256", "bytes32"],
            ["__prefix_free_trial", self._user_address, org_id, service_id, group_id, current_block_number,
             self._free_call_token]
        )
        return service_client.generate_signature(message), current_block_number

    def get_free_call_token_details(self, service_client) -> tuple[bytes, int]:
        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2 = importlib.import_module("state_service_pb2")

        request = state_service_pb2.GetFreeCallTokenRequest(
            address=self._user_address,

        )

        with add_to_path(str(RESOURCES_PATH.joinpath("proto"))):
            state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")

        channel = self.select_channel(service_client)
        stub = state_service_pb2_grpc.FreeCallStateServiceStub(channel)
        response = stub.GetFreeCallToken(request)

        return response.token, response.token_expiration_block
        