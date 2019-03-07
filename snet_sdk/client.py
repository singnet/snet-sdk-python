import sys
import os
from pathlib import PurePath, Path
import importlib
import json

import collections
import grpc
from rfc3986 import urlparse
import web3
from web3.utils.datastructures import AttributeDict, MutableAttributeDict
from eth_account.messages import defunct_hash_message


try:
    main_dir_path = PurePath(os.path.abspath(sys.modules['__main__'].__file__)).parent
except AttributeError:
    main_dir_path = PurePath(os.getcwd())


cur_dir = PurePath(os.path.realpath(__file__)).parent


channel_state_service_proto_path = str(cur_dir.joinpath("resources", "proto"))
sys.path.insert(0, channel_state_service_proto_path)
state_service_pb2 = importlib.import_module("state_service_pb2")
state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")
sys.path.remove(channel_state_service_proto_path)


class _ClientCallDetails(
        collections.namedtuple(
            '_ClientCallDetails',
            ('method', 'timeout', 'metadata', 'credentials')),
        grpc.ClientCallDetails):
    pass


class Client:
    def __init__(
        self,
        snet,
        org_id,
        service_id,
        channel_id
    ):
        self.snet = snet
        self.org_id = org_id
        self.service_id = service_id
        # Import modules and add them to client grpc object
        client_library_path = str(main_dir_path.joinpath(self.snet.libraries_base_path, org_id, service_id))
        sys.path.insert(0, client_library_path)

        grpc_modules = []
        for module_path in Path(client_library_path).glob("**/*_pb2.py"):
            grpc_modules.append(module_path)
        for module_path in Path(client_library_path).glob("**/*_pb2_grpc.py"):
            grpc_modules.append(module_path)

        grpc_modules = list(map(
            lambda x: str(PurePath(Path(x).relative_to(client_library_path).parent.joinpath(PurePath(x).stem))),
            grpc_modules
        ))

        imported_modules = MutableAttributeDict({})
        for grpc_module in grpc_modules:
            imported_module = importlib.import_module(grpc_module)
            imported_modules[grpc_module] = imported_module

        sys.path.remove(client_library_path)


        # Get client metadata for service
        (found, registration_id, metadata_uri, tags) = self.snet.registry_contract.functions.getServiceRegistrationById(bytes(self.org_id, "utf-8"), bytes(self.service_id, "utf-8")).call()
        self.metadata = AttributeDict(json.loads(self.snet.ipfs_client.cat(metadata_uri.rstrip(b"\0").decode('ascii')[7:])))
        default_group = AttributeDict(self.metadata.groups[0])
        self.default_payment_address = default_group["payment_address"]
        default_channel_value = self.metadata.pricing["price_in_cogs"]*100
        default_channel_expiration = int(self.snet.web3.eth.getBlock("latest").number + self.metadata.payment_expiration_threshold + (3600*24*7/self.snet.average_block_time))
        service_endpoint = None
        for endpoint in self.metadata["endpoints"]:
            if (endpoint["group_name"] == default_group["group_name"]):
                service_endpoint = endpoint["endpoint"]
                break


        # Get channel_id for service client
        self._base_grpc_channel = self._get_base_grpc_channel(service_endpoint)

        if channel_id is None:
            self.channel_id = self._get_funded_channel() 

        self.grpc_channel = grpc.intercept_channel(self._base_grpc_channel, generic_client_interceptor.create(self.intercept_call))

        self.open_channel = lambda value=default_channel_value, expiration=default_channel_expiration: _client_open_channel(value, expiration)
        self.get_service_call_metadata = lambda: self._get_service_call_metadata(self.channel_id)
        self.grpc = imported_modules


    # Functions to get a funded channel with a combination of calls to the blockchain and to the daemon 
    def _get_base_grpc_channel(self, endpoint):
        endpoint_object = urlparse(endpoint)
        if endpoint_object.port is not None:
            channel_endpoint = endpoint_object.hostname + ":" + str(endpoint_object.port)
        else: 
            channel_endpoint = endpoint_object.hostname

        if endpoint_object.scheme == "http":
            return grpc.insecure_channel(channel_endpoint)
        elif endpoint_object.scheme == "https":
            return grpc.secure_channel(channel_endpoint, grpc.ssl_channel_credentials())
        else:
            raise ValueError('Unsupported scheme in service metadata ("{}")'.format(endpoint_object.scheme))


    def _get_channel_state(self, channel_id):
        stub = state_service_pb2_grpc.PaymentChannelStateServiceStub(self._base_grpc_channel)
        message = web3.Web3.soliditySha3(["uint256"], [channel_id])
        signature = self.snet.web3.eth.account.signHash(defunct_hash_message(message), self.snet.signer_private_key).signature
        request = state_service_pb2.ChannelStateRequest(channel_id=web3.Web3.toBytes(channel_id), signature=bytes(signature))
        response = stub.GetChannelState(request)
        return {
            "current_nonce": int.from_bytes(response.current_nonce, byteorder="big"),
            "current_signed_amount": int.from_bytes(response.current_signed_amount, byteorder="big")
        }


    def _get_channel_states(self):
        return [dict(self._get_channel_state(channel.channelId), **{"channel_id": channel.channelId, "initial_amount": channel.amount, "expiration": channel.expiration}) for channel in self.snet._get_channels(self.default_payment_address)]


    def _client_open_channel(self, value, expiration):
        mpe_balance = self.snet.mpe_contract.functions.balances(self.snet.address).call()
        group_id = base64.b64decode(default_group.group_id)
        if value > mpe_balance:
            return(self.snet.mpe_deposit_and_open_channel(default_group.payment_address, group_id, value - mpe_balance, expiration))
        else:
            return(self.snet.mpe_open_channel(default_group.payment_address, group_id, value, expiration))


    def _client_add_funds(self, channel_id, amount):
        mpe_balance = self.snet.mpe_contract.functions.balances(self.snet.address).call()
        if value > mpe_balance:
            self.snet.mpe_deposit(amount - mpe_balance)
        return(self.snet.mpe_channel_add_funds(channel_id, amount))


    def _client_extend_and_add_funds(self, channel_id, new_expiration, amount):
        mpe_balance = self.snet.mpe_contract.functions.balances(self.snet.address).call()
        if amount > mpe_balance:
            self.snet.mpe_deposit(amount - mpe_balance)
        return(self.snet.mpe_channel_extend_and_add_funds(channel_id, new_expiration, amount))


    def _get_funded_channel(self):
        channel_states = self._get_channel_states()

        if len(channel_states) == 0:
            if self.snet.allow_transactions is False:
                raise RuntimeError('No state channel found. Please open a new channel or set configuration parameter "allow_transactions=True" when creating Snet class instance')
            else:
                _client_open_channel(default_channel_value, default_channel_expiration)
                channel_states = self._get_channel_states()

        funded_channels = list(filter(lambda state: state["initial_amount"] - state["current_signed_amount"] >= int(self.metadata.pricing["price_in_cogs"]), iter(channel_states)))
        if len(funded_channels) == 0:
            if self.snet.allow_transactions is True:
                non_expired_unfunded_channels = list(filter(lambda state: state["expiration"] + self.metadata.payment_expiration_threshold > self.snet.web3.eth.getBlock("latest").number, iter(channel_states)))
                if len(non_expired_unfunded_channels) == 0:
                    channel_id = next(iter(channel_states))["channel_id"]
                    _client_extend_and_add_funds(channel_id, default_channel_expiration, default_channel_value)
                    return channel_id
                else:
                    channel_id = next(iter(non_expired_unfunded_channels))["channel_id"]
                    _client_add_funds(channel_id, default_channel_value)
                    return channel_id
            else:
                raise RuntimeError('No funded channel found. Please open a new channel or fund an open one, or set configuration parameter "allow_transactions=True" when creating Snet class instance')

        valid_channels = list(filter(lambda state: state["expiration"] + self.metadata.payment_expiration_threshold > self.snet.web3.eth.getBlock("latest").number, iter(funded_channels)))
        if len(valid_channels) == 0:
            if self.snet.allow_transactions is True:
                channel_id = next(iter(funded_channels))["channel_id"]
                self.snet.mpe_channel_extend(channel_id, default_channel_expiration)
                return channel_id
            else:
                raise RuntimeError('No non-expired channel found. Please open a new channel or extend an open and funded one, or set configuration parameter "allow_transactions=True" when creating Snet class instance')
        else:
            channel_id = next(iter(valid_channels))["channel_id"]

        return channel_id


        # Service channel utility methods
        def _get_service_call_metadata(channel_id):
            state = self._get_channel_state(channel_id)
            amount = state["current_signed_amount"] + int(self.metadata.pricing["price_in_cogs"])
            message = web3.Web3.soliditySha3(
                ["address", "uint256", "uint256", "uint256"],
                [self.snet.mpe_contract.address, channel_id, state["current_nonce"], amount]
            )
            signature = bytes(self.snet.web3.eth.account.signHash(defunct_hash_message(message), self.snet.signer_private_key).signature)
            metadata = [
                ("snet-payment-type", "escrow"),
                ("snet-payment-channel-id", str(channel_id)),
                ("snet-payment-channel-nonce", str(state["current_nonce"])),
                ("snet-payment-channel-amount", str(amount)),
                ("snet-payment-channel-signature-bin", signature)
            ]

            return metadata

        # Add request metadata to gRPC service calls
        def intercept_call(self, client_call_details, request_iterator, request_streaming,
                           response_streaming):
            metadata = []
            if client_call_details.metadata is not None:
                metadata = list(client_call_details.metadata)
            metadata.extend(self.get_service_call_metadata())
            client_call_details = _ClientCallDetails(
                client_call_details.method, client_call_details.timeout, metadata,
                client_call_details.credentials)
            return client_call_details, request_iterator, None 
