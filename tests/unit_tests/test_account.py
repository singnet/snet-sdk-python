import os
import unittest
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
from web3 import Web3

from snet.sdk.account import Account, TransactionError
from snet.sdk.config import Config
from snet.sdk.mpe.mpe_contract import MPEContract

load_dotenv()


class TestAccount(unittest.TestCase):
    @patch("snet.sdk.account.get_contract_object")
    def setUp(self, mock_get_contract_object):
        # Mock main fields
        self.mock_web3 = MagicMock(spec=Web3)
        self.mock_config = MagicMock(spec=Config)
        self.mock_mpe_contract = MagicMock(spec=MPEContract)

        # Mock additional fields
        self.mock_web3.eth = MagicMock()
        self.mock_web3.net = MagicMock()
        self.mock_mpe_contract.contract = MagicMock()

        # Config mock return values
        self.mock_config.get.side_effect = lambda key, default=None: {
            "private_key": os.getenv("PRIVATE_KEY"),
            "signer_private_key": None,
            "token_contract_address": None,
        }.get(key, default)

        # Mock token contract
        self.mock_token_contract = MagicMock()
        self.mock_get_contract_object = mock_get_contract_object
        self.mock_get_contract_object.return_value = self.mock_token_contract

        self.account = Account(self.mock_web3, self.mock_config,
                               self.mock_mpe_contract)

    def test_get_nonce(self):
        for i in [4, 5]:
            self.mock_web3.eth.get_transaction_count.return_value = i
            self.account.nonce = 4
            nonce = self.account._get_nonce()
            self.assertEqual(nonce, 5)
            self.assertEqual(self.account.nonce, 5)

    def test_get_gas_price(self):
        # Test different gas price levels
        gas_price = 10000000000
        self.mock_web3.eth.gas_price = gas_price
        result = self.account._get_gas_price()
        self.assertEqual(result, int(gas_price + (gas_price * 1 / 3)))

        gas_price = 16000000000
        self.mock_web3.eth.gas_price = gas_price
        result = self.account._get_gas_price()
        self.assertEqual(result, int(gas_price + (gas_price * 1 / 5)))

        gas_price = 51200000000
        self.mock_web3.eth.gas_price = 51200000000
        result = self.account._get_gas_price()
        self.assertEqual(result, int(gas_price + 7000000000))

        gas_price = 150000000001
        self.mock_web3.eth.gas_price = 150000000001
        result = self.account._get_gas_price()
        self.assertEqual(result, int(gas_price + (gas_price * 1 / 10)))

    # @patch("snet.sdk.web3.Web3.to_hex", side_effect=lambda x: "mock_txn_hash")
    # def test_send_signed_transaction(self, mock_to_hex):
    #     # Mock contract function
    #     mock_contract_fn = MagicMock()
    #     mock_contract_fn.return_value.build_transaction.return_value = {"mock": "txn"}

    #     # Test transaction sending
    #     txn_hash = self.account._send_signed_transaction(mock_contract_fn)
    #     self.assertEqual(txn_hash, "mock_txn_hash")
    #     self.mock_web3.eth.account.sign_transaction.assert_called_once()
    #     self.mock_web3.eth.send_raw_transaction.assert_called_once()

    def test_parse_receipt_success(self):
        # Mock receipt and event
        mock_receipt = MagicMock()
        mock_receipt.status = 1
        mock_event = MagicMock()
        mock_event.return_value.processReceipt.return_value = [
            {"args": {"key": "value"}}
        ]

        result = self.account._parse_receipt(mock_receipt, mock_event)
        self.assertEqual(result, '{"key": "value"}')

    def test_parse_receipt_failure(self):
        # Mock a failing receipt
        mock_receipt = MagicMock()
        mock_receipt.status = 0

        with self.assertRaises(TransactionError) as context:
            self.account._parse_receipt(mock_receipt, None)

        self.assertEqual(str(context.exception), "Transaction failed")
        self.assertEqual(context.exception.receipt, mock_receipt)

    def test_escrow_balance(self):
        self.mock_mpe_contract.balance.return_value = 120000000
        balance = self.account.escrow_balance()
        self.assertIsInstance(balance, int)
        self.assertEqual(balance, 120000000)
        self.mock_mpe_contract.balance.assert_called_once_with(
            self.account.address
        )

    def test_deposit_to_escrow_account(self):
        self.account.allowance = MagicMock(return_value=0)
        self.account.approve_transfer = MagicMock()
        self.mock_mpe_contract.deposit.return_value = "0x51ec7c89064d95416be4"

        result = self.account.deposit_to_escrow_account(100)
        self.account.approve_transfer.assert_called_once_with(100)
        self.mock_mpe_contract.deposit.assert_called_once_with(self.account,
                                                               100)
        self.assertEqual(result, "0x51ec7c89064d95416be4")

    def test_approve_transfer(self):
        self.mock_web3.eth.gas_price = 10000000000
        self.mock_web3.eth.get_transaction_count.return_value = 1
        result = self.account.approve_transfer(500)
        self.assertIsNotNone(result)
        self.mock_token_contract.functions.approve.assert_called_once_with(
            self.mock_mpe_contract.contract.address, 500
        )
    # def test_approve_transfer(self):
    #     self.account.send_transaction = MagicMock()
    #     self.account.send_transaction.return_value = "TxReceipt"
    #     result = self.account.approve_transfer(500)
    #     self.assertEqual(result, "TxReceipt")

    def test_allowance(self):
        self.mock_token_contract.functions.allowance.return_value.call \
            .return_value = 100
        allowance = self.account.allowance()
        self.assertEqual(allowance, 100)
        self.mock_token_contract.functions.allowance.assert_called_once_with(
            self.account.address, self.mock_mpe_contract.contract.address
        )


if __name__ == "__main__":
    unittest.main()
