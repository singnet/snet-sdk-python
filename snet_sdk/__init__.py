import sys
import os 
import importlib
import json
import base64
from pathlib import PurePath, Path
from urllib.parse import urljoin

import ecdsa
import hashlib
import grpc
import web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from eth_account.messages import defunct_hash_message
from rfc3986 import urlparse
import ipfsapi

import snet_sdk.header_manipulator_client_interceptor

__version__ = "0.0.1"

main_dir_path = PurePath(os.path.abspath(sys.modules['__main__'].__file__)).parent
cur_dir = PurePath(os.path.realpath(__file__)).parent


class TransactionError(Exception):
    """Raised when an Ethereum transaction receipt has a status of 0. Can provide a custom message. Optionally includes receipt"""
    def __init__(self, message, receipt=None):
        super().__init__(message)
        self.message = message
        self.receipt = receipt
    def __str__(self):
        return self.message


class ChannelOpenEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) is bytes:
            return base64.b64encode(obj).decode("ascii")
        else:
            super().default(self, obj)


snet_sdk_defaults = {
    "libraries_base_path": "grpc",
    "eth_rpc_endpoint": "https://kovan.infura.io",
    "ipfs_rpc_endpoint": "http://ipfs.singularitynet.io:80",
    "private_key": None,
    "account_index": 0,
    "default_gas": 1000000,
    "mpe_address": None,
    "token_address": None
}


class Snet:
    """Base Snet SDK"""
    def __init__(
        self,
        config=None,
        libraries_base_path=snet_sdk_defaults["libraries_base_path"],
        eth_rpc_endpoint=snet_sdk_defaults["eth_rpc_endpoint"],
        ipfs_rpc_endpoint=snet_sdk_defaults["ipfs_rpc_endpoint"],
        private_key=snet_sdk_defaults["private_key"],
        account_index=snet_sdk_defaults["account_index"],
        default_gas=snet_sdk_defaults["default_gas"],
        mpe_address=snet_sdk_defaults["mpe_address"],
        token_address=snet_sdk_defaults["token_address"]
    ):
        self.libraries_base_path = libraries_base_path
        self.default_gas = default_gas
        self.nonce = 0

        if private_key is not None:
            if private_key.startswith("0x"):
                self.private_key = bytes(bytearray.fromhex(private_key[2:]))
            else:
                self.private_key = bytes(bytearray.fromhex(private_key))

            public_key = ecdsa.SigningKey.from_string(string=self.private_key,
                                                      curve=ecdsa.SECP256k1,
                                                      hashfunc=hashlib.sha256).get_verifying_key()
            self.address = web3.Web3.toChecksumAddress("0x" + web3.Web3.sha3(hexstr=public_key.to_string().hex())[12:].hex())
        else: # Working with an unlocked account, for example
            self.address = web3.Web3.toChecksumAddress(web3.eth.accounts[account_index])

        # Instantiate Ethereum client
        provider = web3.HTTPProvider(eth_rpc_endpoint)
        self.web3 = web3.Web3(provider)
        self.web3.eth.setGasPriceStrategy(rpc_gas_price_strategy)

        # Instantiate IPFS client
        ipfs_rpc_endpoint = urlparse(ipfs_rpc_endpoint)
        ipfs_scheme = ipfs_rpc_endpoint.scheme if ipfs_rpc_endpoint.scheme else "http"
        ipfs_port = ipfs_rpc_endpoint.port if ipfs_rpc_endpoint.port else 5001
        self.ipfs_client = ipfsapi.connect(urljoin(ipfs_scheme, ipfs_rpc_endpoint.hostname), ipfs_port)

        # Get contract objects
        self.mpe_contract = self._get_contract_object("MultiPartyEscrow.json")
        self.token_contract = self._get_contract_object("SingularityNetToken.json")
        self.registry_contract = self._get_contract_object("Registry.json")


    # Generic Eth transaction functions 
    def _get_contract_deployment_block(self, contract_file):
        with open(cur_dir.joinpath("resources", "contracts", "networks", contract_file)) as f:
            networks = json.load(f)
            txn_hash = networks[self.web3.version.network]["transactionHash"]
        return self.web3.eth.getTransactionReceipt(txn_hash).blockNumber

    def _get_nonce(self):
        nonce = self.web3.eth.getTransactionCount(self.address)
        if self.nonce >= nonce:
            nonce = self.nonce + 1
        self.nonce = nonce
        return nonce


    def _get_gas_price(self):
        return self.web3.eth.generateGasPrice()


    def _send_signed_transaction(self, contract_fn, *args):
        transaction = contract_fn(*args).buildTransaction({
            "chainId": int(self.web3.version.network),
            "gas": self.default_gas, 
            "gasPrice": self._get_gas_price(),
            "nonce": self._get_nonce()
        })
        signed_txn = self.web3.eth.account.signTransaction(transaction, private_key=self.private_key)
        return self.web3.toHex(self.web3.eth.sendRawTransaction(signed_txn.rawTransaction))


    def _send_transaction(self, contract_fn, *args):
        if self.private_key is not None:
            txn_hash = self._send_signed_transaction(contract_fn, *args)
        else:
            txn_hash = contract_fn(*args).transact({
                "gas": self.default_gas,
                "gasPrice": gas_price
            })
        return self.web3.eth.waitForTransactionReceipt(txn_hash)


    def _parse_receipt(self, receipt, event, encoder=json.JSONEncoder):
        if receipt.status == 0:
            raise TransactionError("Transaction failed", receipt)
        else:
            return json.dumps(dict(event().processReceipt(receipt)[0]["args"]), cls=encoder)

    def _get_channels(self, recipient_address=None):
        topics = [self.web3.sha3(text="ChannelOpen(uint256,uint256,address,address,address,bytes32,uint256,uint256)").hex()]
        logs = self.web3.eth.getLogs({"fromBlock" : self._get_contract_deployment_block("MultiPartyEscrow.json"), "address": self.mpe_contract.address, "topics": topics})
        event_abi = {'anonymous': False, 'inputs': [{'indexed': False, 'name': 'channelId', 'type': 'uint256'}, {'indexed': False, 'name': 'nonce', 'type': 'uint256'}, {'indexed': True, 'name': 'sender', 'type': 'address'}, {'indexed': False, 'name': 'signer', 'type': 'address'}, {'indexed': True, 'name': 'recipient', 'type': 'address'}, {'indexed': True, 'name': 'groupId', 'type': 'bytes32'}, {'indexed': False, 'name': 'amount', 'type': 'uint256'}, {'indexed': False, 'name': 'expiration', 'type': 'uint256'}], 'name': 'ChannelOpen', 'type': 'event'}
        if recipient_address is None:
            channels = list(filter(lambda channel: channel.sender == self.address, [web3.utils.events.get_event_data(event_abi, l)["args"] for l in logs]))
        else:
            channels = list(filter(lambda channel: channel.sender == self.address and channel.recipient == recipient_address, [web3.utils.events.get_event_data(event_abi, l)["args"] for l in logs]))
        return channels


    # Contract functions 
    def _token_approve_transfer(self, value):
        already_approved = self.token_contract.functions.allowance(self.address, self.mpe_contract.address).call()
        if (already_approved < value):
            self._send_transaction(self.token_contract.functions.approve, self.mpe_contract.address, value - already_approved)


    def mpe_deposit(self, value):
        self._token_approve_transfer(value)
        receipt = self._send_transaction(self.mpe_contract.functions.deposit, value)
        return self._parse_receipt(receipt, self.mpe_contract.events.DepositFunds)


    def mpe_withdraw(self, value):
        receipt = self._send_transaction(self.mpe_contract.functions.withdraw, value)
        return self._parse_receipt(receipt, self.mpe_contract.events.WithdrawFunds)


    def mpe_open_channel(self, recipient_address, group_id, value, expiration):
        receipt = self._send_transaction(self.mpe_contract.functions.openChannel, self.address, recipient_address, group_id, value, expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelOpen, encoder=ChannelOpenEncoder)


    def mpe_deposit_and_open_channel(self, recipient_address, group_id, value, expiration):
        self._token_approve_transfer(value)
        receipt = self._send_transaction(self.mpe_contract.functions.depositAndOpenChannel, self.address, recipient_address, group_id, value, expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelOpen, encoder=ChannelOpenEncoder)


    def mpe_channel_extend(self, channel_id, new_expiration):
        receipt = self._send_transaction(self.mpe_contract.functions.channelExtend, channel_id, new_expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelExtend)


    def mpe_channel_add_funds(self, channel_id, amount):
        receipt = self._send_transaction(self.mpe_contract.functions.channelAddFunds, channel_id, amount)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelAddFunds)

    
    def mpe_channel_extend_and_add_funds(self, channel_id, new_expiration, amount):
        receipt = self._send_transaction(self.mpe_contract.functions.channelExtendAndAddFunds, channel_id, new_expiration, amount)
        return self._parse_receipt(receipt, mpe_contract.events.ChannelAddFunds)


    # Channel utility functions
    def _get_channel_id(self, org_id, service_id):
        raise NotImplementedError("Not yet implemented. Please manually provide a channel id")


    def _get_service_endpoint(self, channel_id):
        raise NotImplementedError("Not yet implemented. Please manually provide service endpoint")


    def _get_org_id_and_service_id(self, channel_id):
        raise NotImplementedError("Not yet implemented. Please manually provide an org id and service id")


    # Generic utility functions
    def _get_contract_object(self, contract_file):
        with open(cur_dir.joinpath("resources", "contracts", "abi", contract_file)) as f:
            abi = json.load(f)
        with open(cur_dir.joinpath("resources", "contracts", "networks", contract_file)) as f:
            networks = json.load(f)
            address = self.web3.toChecksumAddress(networks[self.web3.version.network]["address"])
        return self.web3.eth.contract(abi=abi, address=address)


    # Service client
    def client(self, *args, org_id=None, service_id=None, channel_id=None):
        client = web3.utils.datastructures.MutableAttributeDict({})

        # Determine org_id, service_id and channel_id for client
        _org_id = org_id
        _service_id = service_id
        _channel_id = channel_id

        if len(args) == 2:
            (_org_id, _service_id) = args
        if len(args) == 1:
            raise ValueError("Please either provide both organization id and service id as positional arguments or none of them")

        if (_org_id is not None or _service_id is not None) and (org_id is not None or service_id is not None):
            raise ValueError("Please provide organization id and service id either as positional arguments or as keyword arguments")
        
        if org_id is not None and _service_id is not None:
            _org_id = org_id
            _service_id = service_id

        if _org_id is None or _service_id is None:
            raise ValueError("""Could not instantiate client.
            Please provide at least an org_id and a service_id either as positional or keyword arguments""")


        # Get client metadata for service
        (found, registration_id, metadata_uri, tags) = self.registry_contract.functions.getServiceRegistrationById(bytes(_org_id, "utf-8"), bytes(_service_id, "utf-8")).call()
        client.metadata = web3.utils.datastructures.AttributeDict(json.loads(self.ipfs_client.cat(metadata_uri.rstrip(b"\0").decode('ascii')[7:])))
        default_group = web3.utils.datastructures.AttributeDict(client.metadata.groups[0])
        client.default_payment_address = default_group["payment_address"]
        default_channel_value = client.metadata.pricing["price_in_cogs"]*100
        default_channel_expiration = self.web3.eth.getBlock('latest').number + client.metadata.payment_expiration_threshold+1
        service_endpoint = None
        for endpoint in client.metadata["endpoints"]:
            if (endpoint["group_name"] == default_group["group_name"]):
                service_endpoint = endpoint["endpoint"]
                break


        # Functions to get a funded channel with a combination of calls to the blockchain and to the daemon 
        grpc_channel = grpc.insecure_channel(service_endpoint[7:])

        channel_state_service_proto_path = str(cur_dir.joinpath("resources", "proto"))
        sys.path.insert(0, channel_state_service_proto_path)
        _state_service_pb2 = importlib.import_module("state_service_pb2")
        _state_service_pb2_grpc = importlib.import_module("state_service_pb2_grpc")
        sys.path.remove(channel_state_service_proto_path)


        def _get_channel_state(channel_id):
            stub = _state_service_pb2_grpc.PaymentChannelStateServiceStub(grpc_channel)
            message = web3.Web3.soliditySha3(["uint256"], [channel_id])
            signature = self.web3.eth.account.signHash(defunct_hash_message(message), self.private_key).signature
            request = _state_service_pb2.ChannelStateRequest(channel_id=web3.Web3.toBytes(channel_id), signature=bytes(signature))
            response = stub.GetChannelState(request)
            return {
                "current_nonce": int.from_bytes(response.current_nonce, byteorder="big"),
                "current_signed_amount": int.from_bytes(response.current_signed_amount, byteorder="big")
            }


        def _get_channel_states():
            return [dict(_get_channel_state(channel.channelId), **{"channel_id": channel.channelId, "initial_amount": channel.amount}) for channel in self._get_channels(client.default_payment_address)]


        def _get_funded_channel():
            channel_states = _get_channel_states()
            return next(iter(channel_states), lambda state: state.initial_amount - state.current_signed_amount >= int(client.metadata.pricing["price_in_cogs"]))["channel_id"]


        if _channel_id is None:
            _channel_id = _get_funded_channel() 


        # Import modules and add them to client grpc object
        libraries_base_path = self.libraries_base_path

        client_library_path = str(main_dir_path.joinpath(self.libraries_base_path, _org_id, _service_id))
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

        imported_modules = web3.utils.datastructures.MutableAttributeDict({})
        for grpc_module in grpc_modules:
            imported_module = importlib.import_module(grpc_module)
            imported_modules[grpc_module] = imported_module

        sys.path.remove(client_library_path)


        # Service channel utility methods
        def _client_open_channel(value, expiration):
            mpe_balance = self.mpe_contract.functions.balances(self.address).call()
            group_id = base64.b64decode(default_group.group_id)
            if value > mpe_balance:
                return(self.mpe_deposit_and_open_channel(default_group.payment_address, group_id, value - mpe_balance, expiration))
            else:
                return(self.mpe_open_channel(default_group.payment_address, group_id, value, expiration))


        def _get_channel_signature_bin(channel_id):
            state = _get_channel_state(channel_id)
            '''
            message = web3.Web3.soliditySha3(
                ["address",                 "uint256",  "uint256",              "uint256"],
                [self.mpe_contract.address, channel_id, state["current_nonce"], state["current_signed_amount"] + int(client.metadata.pricing["price_in_cogs"])]
            )
            signature = bytes(self.web3.eth.account.signHash(defunct_hash_message(message), self.private_key))

            '''
            return state


        # Client exports
        client.open_channel = lambda value=default_channel_value, expiration=default_channel_expiration: _client_open_channel(value, expiration)
        client.get_grpc_metadata = lambda: _get_channel_signature_bin(_channel_id)
        client.grpc_channel = grpc_channel
        client.grpc = imported_modules


        return client 
