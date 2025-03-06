import unittest
from unittest.mock import MagicMock, patch

from snet.sdk.mpe.mpe_contract import MPEContract


class TestMPEContract(unittest.TestCase):
    @patch('snet.sdk.mpe.mpe_contract.get_contract_object')
    def setUp(self, mock_get_contract_object):
        self.mock_web3 = MagicMock()
        self.mock_web3.net.version = "1"
        self.mock_contract = MagicMock()
        mock_get_contract_object.return_value = self.mock_contract
        self.mpe_contract = MPEContract(self.mock_web3)
        self.mock_account = MagicMock()
        self.mock_address = "0x123"

    @patch('snet.sdk.mpe.mpe_contract.get_contract_object')
    def test_constructor_with_address(self, mock_get_contract_object):
        address = "0xABC"
        mpe_contract = MPEContract(self.mock_web3, address)
        mock_get_contract_object.assert_called_once_with(
            w3=self.mock_web3,
            contract_file="MultiPartyEscrow",
            address=address
        )

    @patch("snet.sdk.mpe.mpe_contract.get_contract_object")
    def test_init_with_default_address(self, mock_get_contract_object):
        mpe_contract = MPEContract(self.mock_web3)
        mock_get_contract_object.return_value = self.mock_contract
        mock_get_contract_object.assert_called_with(
            w3=self.mock_web3,
            contract_file="MultiPartyEscrow"
        )

    def test_balance(self):
        self.mock_contract.functions.balances.return_value.call.return_value = 100
        result = self.mpe_contract.balance(self.mock_address)
        self.mock_contract.functions.balances.assert_called_once_with(self.mock_address)
        self.mock_contract.functions.balances.return_value.call.assert_called_once()
        self.assertEqual(result, 100)

    def test_deposit(self):
        self.mpe_contract.deposit(self.mock_account, 500)
        self.mock_account.send_transaction.assert_called_once_with(
            self.mock_contract.functions.deposit, 500
        )

    def test_open_channel(self):
        self.mpe_contract.open_channel(
            self.mock_account, "0x456", b"group_id", 1000, 1234567890
        )
        self.mock_account.send_transaction.assert_called_once_with(
            self.mock_contract.functions.openChannel,
            self.mock_account.signer_address,
            "0x456",
            b"group_id",
            1000,
            1234567890
        )

    def test_deposit_and_open_channel_approve_transfer(self):
        self.mock_account.allowance.return_value = 200
        self.mpe_contract.deposit_and_open_channel(
            self.mock_account, "0x456", b"group_id", 1000, 1234567890
        )
        self.mock_account.approve_transfer.assert_called_once_with(1000)
        self.mock_account.send_transaction.assert_called_once_with(
            self.mock_contract.functions.depositAndOpenChannel,
            self.mock_account.signer_address,
            "0x456",
            b"group_id",
            1000,
            1234567890
        )

    def test_channel_add_funds(self):
        with patch.object(self.mpe_contract, 'balance', return_value=500):
            self.mpe_contract.channel_add_funds(self.mock_account, 1, 100)
            self.mock_account.send_transaction.assert_called_once_with(
                self.mock_contract.functions.channelAddFunds, 1, 100
            )

    def test_channel_extend(self):
        self.mpe_contract.channel_extend(self.mock_account, 1, 1234567890)
        self.mock_account.send_transaction.assert_called_once_with(
            self.mock_contract.functions.channelExtend, 1, 1234567890
        )

    def test_channel_extend_and_add_funds(self):
        with patch.object(self.mpe_contract, 'balance', return_value=500):
            self.mpe_contract.channel_extend_and_add_funds(self.mock_account, 1, 1234567890, 100)
            self.mock_account.send_transaction.assert_called_once_with(
                self.mock_contract.functions.channelExtendAndAddFunds, 1, 1234567890, 100
            )

    def test_fund_escrow_account(self):
        with patch.object(self.mpe_contract, 'balance', return_value=300):
            self.mpe_contract._fund_escrow_account(self.mock_account, 500)
            self.mock_account.deposit_to_escrow_account.assert_called_once_with(200)


if __name__ == '__main__':
    unittest.main()
