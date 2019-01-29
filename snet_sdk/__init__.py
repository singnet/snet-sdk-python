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

class Snet:
    def __init__(
        self,
        libraries_base_path="grpc",
        eth_rpc_endpoint="https://kovan.infura.io",
        private_key=None
    ):
        self.libraries_base_path = libraries_base_path
        self.eth_rpc_endpoint = eth_rpc_endpoint
        self.default_gas = 1000000

        if private_key.startswith("0x"):
            self.private_key = bytes(bytearray.fromhex(private_key[2:]))
        else:
            self.private_key = bytes(bytearray.fromhex(private_key))

        public_key = ecdsa.SigningKey.from_string(string=self.private_key,
                                                  curve=ecdsa.SECP256k1,
                                                  hashfunc=hashlib.sha256).get_verifying_key()

        self.address = web3.Web3.toChecksumAddress("0x" + web3.Web3.sha3(hexstr=public_key.to_string().hex())[12:].hex())

        provider = web3.HTTPProvider(eth_rpc_endpoint)
        self.web3 = web3.Web3(provider)
        self.web3.eth.setGasPriceStrategy(rpc_gas_price_strategy)

        with open(cur_dir.joinpath("resources", "contracts", "abi", "MultiPartyEscrow.json")) as f:
            mpe_abi = json.load(f)
        with open(cur_dir.joinpath("resources", "contracts", "networks", "MultiPartyEscrow.json")) as f:
            mpe_networks = json.load(f)

        with open(cur_dir.joinpath("resources", "contracts", "abi", "SingularityNetToken.json")) as f:
            token_abi = json.load(f)
        with open(cur_dir.joinpath("resources", "contracts", "networks", "SingularityNetToken.json")) as f:
            token_networks = json.load(f)

        self.mpe_contract = self.web3.eth.contract(abi=mpe_abi, address=self.web3.toChecksumAddress(mpe_networks[self.web3.version.network]["address"]))
        self.token_contract = self.web3.eth.contract(abi=token_abi, address=self.web3.toChecksumAddress(token_networks[self.web3.version.network]["address"]))

    def _build_transaction(self, contract_fn, *args):
        nonce = self.web3.eth.getTransactionCount(self.address)
        gas_price = self.web3.eth.generateGasPrice()
        gas_limit = self.default_gas
        transaction = contract_fn(*args).buildTransaction({
            "chainId": int(self.web3.version.network),
            "gas": gas_limit,
            "gasPrice": gas_price,
            "nonce": nonce
        })
        return transaction
    

    def _sign_and_send_transaction(self, transaction):
        signed_txn = self.web3.eth.account.signTransaction(transaction, private_key=self.private_key)
        return self.web3.toHex(self.web3.eth.sendRawTransaction(signed_txn.rawTransaction))


    def mpe_deposit(self, value):
        already_approved = self.token_contract.functions.allowance(self.address, self.mpe_contract.address).call()
        if (already_approved < value):
            txn = self._build_transaction(self.token_contract.functions.approve, self.mpe_contract.address, value)
            txn_hash = self._sign_and_send_transaction(txn)
            receipt = self.web3.eth.waitForTransactionReceipt(txn_hash)
        txn = self._build_transaction(self.mpe_contract.functions.deposit, value)
        return self._sign_and_send_transaction(txn)


    def mpe_withdraw(self, value):
        txn = self._build_transaction(self.mpe_contract.functions.withdraw, value)
        return self._sign_and_send_transaction(txn)


    def channel_open(self, client, value, expiration):
        txn = self._build_transaction(self.mpe_contract.functions.openChannel, self.address, client.recipient_address, client.group_id, value, expiration)
        return self._sign_and_send_transaction(txn)


    def channel_deposit_and_open(self, client, value, expiration):
        self.web3.eth.waitForTransactionReceipt(self.mpe_deposit(value))
        txn = self._build_transaction(self.mpe_contract.functions.depositAndOpenChannel, self.address, client.recipient_address, client.group_id, value, expiration)
        return self._sign_and_send_transaction(txn)


    def channel_extend(self, channel_id, new_expiration):
        txn = self._build_transaction(self.mpe_contract.functions.channelExtend, channel_id, new_expiration)
        return self._sign_and_send_transaction(txn)


    def channel_add_funds(self, channel_id, amount):
        txn = self._build_transaction(self.mpe_contract.functions.channelAddFunds, channel_id, amount)
        return self._sign_and_send_transaction(txn)

    
    def channel_extend_and_add_funds(self, channel_id, new_expiration, amount):
        txn = self._build_transaction(self.mpe_contract.functions.channelExtendAndAddFunds, channel_id, new_expiration, amount)
        return self._sign_and_send_transaction(txn)


    def client(self, _org_id, _service_id, service_endpoint):
        client = {}

        # Import modules and add them to client grpc object
        libraries_base_path = self.libraries_base_path
        org_id = _org_id
        service_id = _service_id 

        client_library_path = str(main_dir_path.joinpath(self.libraries_base_path, org_id, service_id))
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
        client["grpc"] = imported_modules

        grpc_channel = grpc.insecure_channel(service_endpoint)
        client["grpc_channel"] = grpc_channel

        return client 
