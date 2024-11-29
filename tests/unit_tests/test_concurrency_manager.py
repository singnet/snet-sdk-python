import unittest
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
from web3 import Web3

from snet.sdk.concurrency_manager import ConcurrencyManager
from snet.sdk.mpe.mpe_contract import MPEContract
from snet.sdk.service_client import ServiceClient

load_dotenv()


class TestConcurrencyManager(unittest.TestCase):
    def setUp(self):
        self.mock_service_client = MagicMock(spec=ServiceClient)
        self.mock_service_client.sdk_web3 = MagicMock(spec=Web3)
        self.mock_service_client.sdk_web3.eth = MagicMock()
        self.mock_service_client.mpe_address = MagicMock(spec=MPEContract)
        self.mock_channel = MagicMock(
            state={"last_signed_amount": 0, "nonce": 1}
        )
        self.manager = ConcurrencyManager(concurrent_calls=5)

    def test_concurrent_calls_property(self):
        self.assertEqual(self.manager.concurrent_calls, 5)

    def test_get_token_old(self):
        with patch.object(
            self.manager,
            "_ConcurrencyManager__get_token_for_amount"
        ) as mock_get_token_for_amount:
            mock_get_token_for_amount.return_value = MagicMock(
                token="mock_token", planned_amount=7, used_amount=2
            )

            token = self.manager.get_token(
                self.mock_service_client,
                self.mock_channel,
                service_call_price=1
            )
            self.assertEqual(token, "mock_token")
            self.assertEqual(
                self.manager._ConcurrencyManager__used_amount, 2
            )
            self.assertEqual(
                self.manager._ConcurrencyManager__planned_amount, 7
            )

    def test_get_token_old_with_last_signed_amount(self):
        self.mock_channel.state["last_signed_amount"] = 1
        with patch.object(
            self.manager,
            "_ConcurrencyManager__get_token_for_amount"
        ) as mock_get_token_for_amount:
            mock_get_token_for_amount.return_value = MagicMock(
                token="mock_token", planned_amount=2, used_amount=7
            )

            token = self.manager.get_token(
                self.mock_service_client,
                self.mock_channel,
                service_call_price=1
            )
            self.assertEqual(token, "mock_token")
            self.assertEqual(
                self.manager._ConcurrencyManager__used_amount, 7
            )
            self.assertEqual(
                self.manager._ConcurrencyManager__planned_amount, 2
            )

        self.manager._ConcurrencyManager__token = ""
        with patch.object(
            self.manager,
            "_ConcurrencyManager__get_token_for_amount"
        ) as mock_get_token_for_amount:
            mock_get_token_for_amount.return_value = MagicMock(
                token="mock_token", planned_amount=7, used_amount=2
            )

            token = self.manager.get_token(
                self.mock_service_client,
                self.mock_channel,
                service_call_price=1
            )
            self.assertEqual(token, "mock_token")
            self.assertEqual(
                self.manager._ConcurrencyManager__used_amount, 2
            )
            self.assertEqual(
                self.manager._ConcurrencyManager__planned_amount, 7
            )

    def test_get_token_new(self):
        self.manager._ConcurrencyManager__token = "test"
        with patch.object(
            self.manager,
            "_ConcurrencyManager__get_token_for_amount"
        ) as mock_get_token_for_amount:
            mock_get_token_for_amount.return_value = MagicMock(
                token="mock_token", planned_amount=7, used_amount=2
            )

            token = self.manager.get_token(
                self.mock_service_client,
                self.mock_channel,
                service_call_price=1
            )
            self.assertEqual(token, "mock_token")
            self.assertEqual(
                self.manager._ConcurrencyManager__used_amount, 2
            )
            self.assertEqual(
                self.manager._ConcurrencyManager__planned_amount, 7
            )

    def test_get_token_reuse_existing_token(self):
        self.manager._ConcurrencyManager__token = "existing_token"
        self.manager._ConcurrencyManager__planned_amount = 5
        self.manager._ConcurrencyManager__used_amount = 3

        token = self.manager.get_token(self.mock_service_client,
                                       self.mock_channel,
                                       service_call_price=1)
        self.assertEqual(token, "existing_token")

    @patch("snet.sdk.concurrency_manager.importlib.import_module")
    def test_get_stub_for_get_token(self, mock_import_module):
        mock_grpc_stub = MagicMock()
        mock_import_module.return_value = MagicMock(
            TokenServiceStub=mock_grpc_stub
        )
        stub = self.manager._ConcurrencyManager__get_stub_for_get_token(
            self.mock_service_client
        )
        self.assertEqual(stub, mock_grpc_stub())

    @patch("snet.sdk.concurrency_manager.web3.Web3.solidity_keccak")
    @patch("snet.sdk.concurrency_manager.importlib.import_module")
    def test_get_token_for_amount(self, mock_import_module,
                                  mock_solidity_keccak):
        mock_stub = MagicMock()
        mock_import_module.return_value = MagicMock(
            TokenServiceStub=MagicMock(return_value=mock_stub)
        )
        mock_stub.GetToken.return_value = MagicMock(
            token="mock_token", planned_amount=15, used_amount=5
        )
        self.mock_service_client.sdk_web3.eth.get_block.return_value = (
            MagicMock(number=1234)
        )
        self.mock_service_client.generate_signature.side_effect = [
            b"sig1", b"sig2"
        ]

        token_reply = self.manager._ConcurrencyManager__get_token_for_amount(
            self.mock_service_client, self.mock_channel, amount=100
        )
        self.assertEqual(token_reply.token, "mock_token")
        self.assertEqual(token_reply.planned_amount, 15)
        self.assertEqual(token_reply.used_amount, 5)
        mock_stub.GetToken.assert_called_once()
        self.mock_service_client.generate_signature.assert_called()

    def test_record_successful_call(self):
        self.manager.record_successful_call()
        self.assertEqual(self.manager._ConcurrencyManager__used_amount, 1)
        self.manager.record_successful_call()
        self.assertEqual(self.manager._ConcurrencyManager__used_amount, 2)


if __name__ == "__main__":
    unittest.main()
