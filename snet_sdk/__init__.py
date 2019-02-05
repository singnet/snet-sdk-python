import sys
import os 
import importlib
import json
from pathlib import PurePath, Path

import ecdsa
import hashlib
import grpc
import web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy

import snet_sdk.header_manipulator_client_interceptor

__version__ = "0.0.1"

main_dir_path = PurePath(os.path.abspath(sys.modules['__main__'].__file__)).parent
cur_dir = PurePath(os.path.realpath(__file__)).parent

snet_sdk_defaults = {
    "libraries_base_path": "grpc",
    "eth_rpc_endpoint": "https://kovan.infura.io",
    "private_key": None,
    "account_index": 0,
    "default_gas": 1000000,
    "mpe_address": None,
    "token_address": None
}

class TransactionError(Exception):
    """Raised when an Ethereum transaction receipt has a status of 0. Can provide a custom message. Optionally includes receipt"""
    def __init__(self, message, receipt=None):
        super().__init__(message)
        self.message = message
        self.receipt = receipt
    def __str__(self):
        return self.message

class Snet:
    """Base Snet SDK"""
    def __init__(
        self,
        config=None,
        libraries_base_path=snet_sdk_defaults["libraries_base_path"],
        eth_rpc_endpoint=snet_sdk_defaults["eth_rpc_endpoint"],
        private_key=snet_sdk_defaults["private_key"],
        account_index=snet_sdk_defaults["account_index"],
        default_gas=snet_sdk_defaults["default_gas"],
        mpe_address=snet_sdk_defaults["mpe_address"],
        token_address=snet_sdk_defaults["token_address"]
    ):
        self.libraries_base_path = libraries_base_path
        self.eth_rpc_endpoint = eth_rpc_endpoint
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

        provider = web3.HTTPProvider(eth_rpc_endpoint)
        self.web3 = web3.Web3(provider)
        self.web3.eth.setGasPriceStrategy(rpc_gas_price_strategy)

        with open(cur_dir.joinpath("resources", "contracts", "abi", "MultiPartyEscrow.json")) as f:
            mpe_abi = json.load(f)
        with open(cur_dir.joinpath("resources", "contracts", "networks", "MultiPartyEscrow.json")) as f:
            mpe_networks = json.load(f)
            if mpe_address is None:
                self.mpe_address = self.web3.toChecksumAddress(mpe_networks[self.web3.version.network]["address"])
            else:
                self.mpe_address = mpe_address

        with open(cur_dir.joinpath("resources", "contracts", "abi", "SingularityNetToken.json")) as f:
            token_abi = json.load(f)
        with open(cur_dir.joinpath("resources", "contracts", "networks", "SingularityNetToken.json")) as f:
            token_networks = json.load(f)
            if token_address is None:
                self.token_address = self.web3.toChecksumAddress(token_networks[self.web3.version.network]["address"])
            else:
                self.token_address = token_address

        self.mpe_contract = self.web3.eth.contract(abi=mpe_abi, address=self.mpe_address)
        self.token_contract = self.web3.eth.contract(abi=token_abi, address=self.token_address)


    # GENERIC ETH TRANSACTION FUNCTIONS
    def _get_nonce(self):
        nonce = self.web3.eth.getTransactionCount(self.address)
        if self.nonce >= nonce:
            nonce = self.nonce + 1
        self.nonce = nonce
        return nonce


    def _get_gas_price(self):
        return self.web3.eth.generateGasPrice()


    def _send_signed_transaction(self, contract_fn, *args):
        gas_limit = self.default_gas
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
                "gas": gas_limit,
                "gasPrice": gas_price
            })
        return self.web3.eth.waitForTransactionReceipt(txn_hash)


    def _parse_receipt(self, receipt, event):
        if receipt.status == 0:
            raise TransactionError("Transaction failed", receipt)
        else:
            return event().processReceipt(receipt)[0]["args"]


    # CONTRACT FUNCTIONS
    def mpe_deposit(self, value):
        already_approved = self.token_contract.functions.allowance(self.address, self.mpe_contract.address).call()
        if (already_approved < value):
            self._send_transaction(self.token_contract.functions.approve, self.mpe_contract.address, value)
        receipt = self._send_transaction(self.mpe_contract.functions.deposit, value)
        return self._parse_receipt(receipt, self.mpe_contract.events.DepositFunds)


    def mpe_withdraw(self, value):
        receipt = self._send_transaction(self.mpe_contract.functions.withdraw, value)
        return self._parse_receipt(receipt, self.mpe_contract.events.WithdrawFunds)


    def mpe_open_channel(self, recipient_address, group_id, value, expiration):
        receipt = self._send_transaction(self.mpe_contract.functions.openChannel, self.address, recipient_address, group_id, value, expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelOpen)


    def mpe_deposit_and_open_channel(self, recipient_address, group_id, value, expiration):
        receipt = self._send_transaction(self.mpe_contract.functions.depositAndOpenChannel, self.address, recipient_address, group_id, value, expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelOpen)


    def mpe_channel_extend(self, channel_id, new_expiration):
        receipt = self._send_transaction(self.mpe_contract.functions.channelExtend, channel_id, new_expiration)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelExtend)


    def mpe_channel_add_funds(self, channel_id, amount):
        receipt = self._send_transaction(self.mpe_contract.functions.channelAddFunds, channel_id, amount)
        return self._parse_receipt(receipt, self.mpe_contract.events.ChannelAddFunds)

    
    def mpe_channel_extend_and_add_funds(self, channel_id, new_expiration, amount):
        receipt = self._send_transaction(self.mpe_contract.functions.channelExtendAndAddFunds, channel_id, new_expiration, amount)
        return self._parse_receipt(receipt, mpe_contract.events.ChannelAddFunds)


    # CHANNEL UTILITY FUNCTIONS
    def _get_channel_id(self, org_id, service_id):
        raise NotImplementedError("Not yet implemented. Please manually provide a channel id")

    def _get_service_endpoint(self, channel_id):
        raise NotImplementedError("Not yet implemented. Please manually provide service endpoint")

    def _get_org_id_and_service_id(self, channel_id):
        raise NotImplementedError("Not yet implemented. Please manually provide an org id and service id")

    # SERVICE CLIENT
    def client(self, *args, org_id=None, service_id=None, channel_id=None, service_endpoint=None):
        _org_id = org_id
        _service_id = service_id
        _channel_id = channel_id
        _service_endpoint = service_endpoint

        if len(args) == 2:
            (_org_id, _service_id) = args
        if len(args) == 1:
            raise ValueError("Please either provide both organization id and service id as positional arguments or none of them")

        if (_org_id is not None or _service_id is not None) and (org_id is not None or service_id is not None):
            raise ValueError("Please provide organization id and service id either as positional arguments or as keyword arguments")
        
        if org_id is not None and _service_id is not None:
            _org_id = org_id
            _service_id = service_id

        if (_org_id is None or _service_id is None) and _channel_id is not None:
            (_org_id, _service_id) = self._get_org_id_and_service_id(_channel_id)

        if _org_id is not None and _service_id is not None and _channel_id is None:
            _channel_id = self._get_channel_id(_org_id, _service_id)

        if _service_endpoint is None:
            _service_endpoint = self._get_service_endpoint(_channel_id)


        if _org_id is None or _service_id is None or _channel_id is None or _service_endpoint is None:
            raise ValueError("""Could not instantiate client.
            Please provide at least a client_id and an org_id and a service_id either as positional or keyword arguments""")


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

        imported_modules = {}
        for grpc_module in grpc_modules:
            imported_module = importlib.import_module(grpc_module)
            imported_modules[grpc_module] = imported_module

        sys.path.remove(client_library_path)

        client = {}

        client["grpc"] = imported_modules

        grpc_channel = grpc.insecure_channel(_service_endpoint)
        client["grpc_channel"] = grpc_channel

        return client 
