import json

from snet.sdk.utils.utils import get_address_from_private, normalize_private_key
from snet.contracts import get_contract_object

DEFAULT_GAS = 300000
TRANSACTION_TIMEOUT = 500


class TransactionError(Exception):
    """Raised when an Ethereum transaction receipt has a status of 0. Can provide a custom message. Optionally includes receipt"""

    def __init__(self, message, receipt=None):
        super().__init__(message)
        self.message = message
        self.receipt = receipt

    def __str__(self):
        return self.message


class Account:
    def __init__(self, w3, config, mpe_contract):
        self.config = config
        self.web3 = w3
        self.mpe_contract = mpe_contract
        _token_contract_address = self.config.get("token_contract_address", None)
        if _token_contract_address is None:
            self.token_contract = get_contract_object(
                self.web3, "SingularityNetToken")
        else:
            self.token_contract = get_contract_object(
                self.web3, "SingularityNetToken", _token_contract_address)

        private_key = config.get("private_key", None)
        signer_private_key = config.get("signer_private_key", None)
        if private_key is not None:
            self.private_key = normalize_private_key(config["private_key"])
        if signer_private_key is not None:
            self.signer_private_key = normalize_private_key(
                config["signer_private_key"])
        else:
            self.signer_private_key = self.private_key
        self.address = get_address_from_private(self.private_key)
        self.signer_address = get_address_from_private(self.signer_private_key)
        self.nonce = 0

    def _get_nonce(self):
        nonce = self.web3.eth.get_transaction_count(self.address)
        if self.nonce >= nonce:
            nonce = self.nonce + 1
        self.nonce = nonce
        return nonce

    def _get_gas_price(self):
        gas_price = self.web3.eth.gas_price
        if gas_price <= 15000000000:
            gas_price += gas_price * 1 / 3
        elif gas_price > 15000000000 and gas_price <= 50000000000:
            gas_price += gas_price * 1 / 5
        elif gas_price > 50000000000 and gas_price <= 150000000000:
            gas_price += 7000000000
        elif gas_price > 150000000000:
            gas_price += gas_price * 1 / 10
        return int(gas_price)

    def _send_signed_transaction(self, contract_fn, *args):
        transaction = contract_fn(*args).build_transaction({
            "chainId": int(self.web3.net.version),
            "gas": DEFAULT_GAS,
            "gasPrice": self._get_gas_price(),
            "nonce": self._get_nonce()
        })
        signed_txn = self.web3.eth.account.sign_transaction(
            transaction, private_key=self.private_key)
        return self.web3.to_hex(self.web3.eth.send_raw_transaction(signed_txn.rawTransaction))

    def send_transaction(self, contract_fn, *args):
        txn_hash = self._send_signed_transaction(contract_fn, *args)
        return self.web3.eth.wait_for_transaction_receipt(txn_hash, TRANSACTION_TIMEOUT)

    def _parse_receipt(self, receipt, event, encoder=json.JSONEncoder):
        if receipt.status == 0:
            raise TransactionError("Transaction failed", receipt)
        else:
            return json.dumps(dict(event().processReceipt(receipt)[0]["args"]), cls=encoder)

    def escrow_balance(self):
        return self.mpe_contract.balance(self.address)

    def deposit_to_escrow_account(self, amount_in_cogs):
        already_approved = self.allowance()
        if amount_in_cogs > already_approved:
            self.approve_transfer(amount_in_cogs)
        return self.mpe_contract.deposit(self, amount_in_cogs)

    def approve_transfer(self, amount_in_cogs):
        return self.send_transaction(self.token_contract.functions.approve, self.mpe_contract.contract.address,
                                     amount_in_cogs)

    def allowance(self):
        return self.token_contract.functions.allowance(self.address, self.mpe_contract.contract.address).call()
