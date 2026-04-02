from typing import Optional

from snet.contracts import get_contract_object

from snet.sdk.account import Account
from snet.sdk.config import config
from snet.sdk.utils.utils import get_we3_object


class MPEContract:
    def __init__(self):
        self.w3 = get_we3_object()
        self.contract = get_contract_object(
            self.w3, "MultiPartyEscrow", config.MPE_CONTRACT_ADDRESS
        )

    def balance(self, account: Account, address: Optional[str] = None):
        if not address:
            address = account.address
        return self.contract.functions.balances(address).call()

    def deposit(self, account: Account, amount_in_cogs: int):
        already_approved = account.allowance()
        if amount_in_cogs > already_approved:
            account.approve_transfer(amount_in_cogs)
        return account.send_transaction(self.contract.functions.deposit, amount_in_cogs)

    def open_channel(self, account: Account, payment_address, group_id, amount, expiration):
        return account.send_transaction(
            self.contract.functions.openChannel,
            account.signer_address,
            payment_address,
            group_id,
            amount,
            expiration,
        )

    def deposit_and_open_channel(
        self, account: Account, payment_address, group_id, amount, expiration
    ):
        already_approved_amount = account.allowance()
        if amount > already_approved_amount:
            account.approve_transfer(amount)
        return account.send_transaction(
            self.contract.functions.depositAndOpenChannel,
            account.signer_address,
            payment_address,
            group_id,
            amount,
            expiration,
        )

    def channel_add_funds(self, account: Account, channel_id, amount):
        self._fund_escrow_account(account, amount)
        return account.send_transaction(self.contract.functions.channelAddFunds, channel_id, amount)

    def channel_extend(self, account: Account, channel_id, expiration):
        return account.send_transaction(
            self.contract.functions.channelExtend, channel_id, expiration
        )

    def channel_extend_and_add_funds(self, account: Account, channel_id, expiration, amount):
        self._fund_escrow_account(account, amount)
        return account.send_transaction(
            self.contract.functions.channelExtendAndAddFunds,
            channel_id,
            expiration,
            amount,
        )

    def _fund_escrow_account(self, account: Account, amount):
        current_escrow_balance = self.balance(account)
        if amount > current_escrow_balance:
            self.deposit(account, amount - current_escrow_balance)
