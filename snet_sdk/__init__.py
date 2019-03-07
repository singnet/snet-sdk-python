import operator
from functools import reduce
import sys
import os 
import importlib
import json
import base64
from pathlib import PurePath, Path
from urllib.parse import urljoin

import ecdsa
import hashlib
import collections
import web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from eth_account.messages import defunct_hash_message
from rfc3986 import urlparse
import ipfsapi
from web3.utils.datastructures import AttributeDict, MutableAttributeDict

import snet_sdk.generic_client_interceptor as generic_client_interceptor
from snet_sdk.client import Client

__version__ = "0.0.1"

try:
    main_dir_path = PurePath(os.path.abspath(sys.modules['__main__'].__file__)).parent
except AttributeError:
    main_dir_path = PurePath(os.getcwd())

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
    "signer_private_key": None,
    "account_index": 0,
    "default_gas": 1000000,
    "mpe_address": None,
    "token_address": None,
    "allow_transactions": False
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
        signer_private_key=snet_sdk_defaults["signer_private_key"],
        account_index=snet_sdk_defaults["account_index"],
        default_gas=snet_sdk_defaults["default_gas"],
        mpe_address=snet_sdk_defaults["mpe_address"],
        token_address=snet_sdk_defaults["token_address"],
        allow_transactions=snet_sdk_defaults["allow_transactions"]
    ):
        self.libraries_base_path = libraries_base_path
        self.default_gas = default_gas
        self.allow_transactions = allow_transactions
        self.nonce = 0
        self.logs = None

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


        if self.private_key is not None and signer_private_key is None:
            self.signer_private_key = self.private_key
        else:
            self.signer_private_key = signer_private_key

        signer_public_key = ecdsa.SigningKey.from_string(string=self.private_key,
                                                  curve=ecdsa.SECP256k1,
                                                  hashfunc=hashlib.sha256).get_verifying_key()

        self.signer_address = web3.Web3.toChecksumAddress("0x" + web3.Web3.sha3(hexstr=signer_public_key.to_string().hex())[12:].hex())


        # Instantiate Ethereum client
        provider = web3.HTTPProvider(eth_rpc_endpoint)
        self.web3 = web3.Web3(provider)
        self.web3.eth.setGasPriceStrategy(rpc_gas_price_strategy)

        # Get average block time for current network
        latest = self.web3.eth.getBlock("latest")
        times = [block.timestamp for block in list(map(lambda n: self.web3.eth.getBlock(n), range(latest.number, latest.number-20, -1)))]
        diffs = list(map(operator.sub, times[1:], times[:-1]))
        self.average_block_time = abs(reduce(lambda a, b: a+b, diffs) / len(diffs))

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


    def _update_channel_data_from_blockchain(self, channel):
        channel_blockchain_data = self.mpe_contract.functions.channels(channel["channelId"]).call()
        channel = dict(channel)
        channel["nonce"] = channel_blockchain_data[0]
        channel["amount"] = channel_blockchain_data[5]
        channel["expiration"] = channel_blockchain_data[6]
        return AttributeDict(channel)


    def _get_channels(self, recipient_address=None):
        topics = [self.web3.sha3(text="ChannelOpen(uint256,uint256,address,address,address,bytes32,uint256,uint256)").hex()]
        if self.logs is None:
            self.logs = self.web3.eth.getLogs({"fromBlock" : self._get_contract_deployment_block("MultiPartyEscrow.json"), "address": self.mpe_contract.address, "topics": topics})
        event_abi = {'anonymous': False, 'inputs': [{'indexed': False, 'name': 'channelId', 'type': 'uint256'}, {'indexed': False, 'name': 'nonce', 'type': 'uint256'}, {'indexed': True, 'name': 'sender', 'type': 'address'}, {'indexed': False, 'name': 'signer', 'type': 'address'}, {'indexed': True, 'name': 'recipient', 'type': 'address'}, {'indexed': True, 'name': 'groupId', 'type': 'bytes32'}, {'indexed': False, 'name': 'amount', 'type': 'uint256'}, {'indexed': False, 'name': 'expiration', 'type': 'uint256'}], 'name': 'ChannelOpen', 'type': 'event'}
        if recipient_address is None:
            channels = list(filter(lambda channel: channel.sender == self.address and channel.signer == self.signer_address, [web3.utils.events.get_event_data(event_abi, l)["args"] for l in self.logs]))
        else:
            channels = list(filter(lambda channel: channel.sender == self.address and channel.signer == self.signer_address and channel.recipient == recipient_address, [web3.utils.events.get_event_data(event_abi, l)["args"] for l in self.logs]))

        return list(map(lambda c: self._update_channel_data_from_blockchain(c), channels))


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
        receipt = self._send_transaction(self.mpe_contract.functions.openChannel, self.signer_address, recipient_address, group_id, value, expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelOpen, encoder=ChannelOpenEncoder)


    def mpe_deposit_and_open_channel(self, recipient_address, group_id, value, expiration):
        self._token_approve_transfer(value)
        receipt = self._send_transaction(self.mpe_contract.functions.depositAndOpenChannel, self.signer_address, recipient_address, group_id, value, expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelOpen, encoder=ChannelOpenEncoder)


    def mpe_channel_extend(self, channel_id, new_expiration):
        receipt = self._send_transaction(self.mpe_contract.functions.channelExtend, channel_id, new_expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelExtend)


    def mpe_channel_add_funds(self, channel_id, amount):
        receipt = self._send_transaction(self.mpe_contract.functions.channelAddFunds, channel_id, amount)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelAddFunds)

    
    def mpe_channel_extend_and_add_funds(self, channel_id, new_expiration, amount):
        receipt = self._send_transaction(self.mpe_contract.functions.channelExtendAndAddFunds, channel_id, new_expiration, amount)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelAddFunds)


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

        client = Client(self, _org_id, _service_id, _channel_id)
        return client
