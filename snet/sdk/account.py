from typing import Callable, Optional, Union

from hexbytes import HexBytes
from snet.contracts import get_contract_object
from web3.contract.contract import ContractEvent
from web3.exceptions import TimeExhausted
from web3.types import TxReceipt, EventData

from snet.sdk.config import config
from snet.sdk.exceptions import (
    TransactionTimeoutError,
    TransactionRevertedError,
    EventNotFoundError,
)
from snet.sdk.utils.utils import get_address_from_private, normalize_private_key, get_we3_object

DEFAULT_GAS = 300000
TRANSACTION_TIMEOUT = 500


class Account:
    def __init__(self, mpe_address: str):
        self.w3 = get_we3_object()
        self.mpe_address = mpe_address

        self.token_contract = get_contract_object(
            self.w3, "FetchToken", config.TOKEN_CONTRACT_ADDRESS
        )

        if config.PRIVATE_KEY:
            self.private_key = normalize_private_key(config.PRIVATE_KEY)
        if config.SIGNER_PRIVATE_KEY:
            self.signer_private_key = normalize_private_key(config.SIGNER_PRIVATE_KEY)
        else:
            self.signer_private_key = self.private_key

        self.address = get_address_from_private(self.private_key)
        self.signer_address = get_address_from_private(self.signer_private_key)
        self.nonce = 0

    def _get_nonce(self):
        nonce = self.w3.eth.get_transaction_count(self.address)
        if self.nonce >= nonce:
            nonce = self.nonce + 1
        self.nonce = nonce
        return nonce

    def _get_gas_price(self):
        gas_price = self.w3.eth.gas_price
        if gas_price <= 15000000000:
            gas_price += gas_price * 1 / 3
        elif 15000000000 < gas_price <= 50000000000:
            gas_price += gas_price * 1 / 5
        elif 50000000000 < gas_price <= 150000000000:
            gas_price += 7000000000
        elif gas_price > 150000000000:
            gas_price += gas_price * 1 / 10
        return int(gas_price)

    def _send_signed_transaction(self, contract_fn, *args) -> HexBytes:
        try:
            estimated_gas = contract_fn(*args).estimate_gas({"from": self.address})
            gas_limit = int(estimated_gas * 1.2)
        except Exception:
            gas_limit = DEFAULT_GAS

        transaction = contract_fn(*args).build_transaction(
            {
                "chainId": self.w3.eth.chain_id,
                "gas": gas_limit,
                "gasPrice": self._get_gas_price(),
                "nonce": self._get_nonce(),
            }
        )

        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
        return self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    def send_transaction(
        self, contract_fn: Callable, *args, event: Optional[ContractEvent] = None
    ) -> Union[TxReceipt, EventData]:
        txn_hash = self._send_signed_transaction(contract_fn, *args)

        try:
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(
                txn_hash, timeout=TRANSACTION_TIMEOUT
            )
        except TimeExhausted:
            raise TransactionTimeoutError(self.w3.to_hex(txn_hash), TRANSACTION_TIMEOUT)

        if event is not None:
            return self._parse_receipt(tx_receipt, event)

        return tx_receipt

    def _parse_receipt(self, receipt: TxReceipt, event: ContractEvent) -> EventData:
        if receipt["status"] == 0:
            raise TransactionRevertedError(self.w3.to_hex(receipt["transactionHash"]))

        processed_logs = event().process_receipt(receipt)

        if not processed_logs:
            raise EventNotFoundError(self.w3.to_hex(receipt["transactionHash"]), event.event_name)

        return processed_logs[0]

    def approve_transfer(self, amount_in_cogs):
        return self.send_transaction(
            self.token_contract.functions.approve,
            self.mpe_address,
            amount_in_cogs,
        )

    def allowance(self):
        return self.token_contract.functions.allowance(self.address, self.mpe_address).call()
