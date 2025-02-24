from pathlib import Path
import unittest
from unittest.mock import MagicMock, Mock, patch, create_autospec

from web3 import Web3

from snet.sdk.account import Account
from snet.sdk.mpe.mpe_contract import MPEContract
from snet.sdk.mpe.payment_channel_provider import PaymentChannelProvider
from snet.sdk.service_client import ServiceClient
from snet.sdk.storage_provider.service_metadata import MPEServiceMetadata


class TestServiceClient(unittest.TestCase):
    def setUp(self):
        self.mock_org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
        self.mock_service_id = "Exampleservice"
        self.mock_service_metadata = MagicMock(spec=MPEServiceMetadata)
        self.mock_group = {
            'free_calls': 0,
            'free_call_signer_address': '0x7DF35C98f41F3Af0df1dc4c7F7D4C19a71Dd059F',
            'daemon_addresses': [
                '0x0709e9b78756b740ab0c64427f43f8305fd6d1a7'
            ],
            'pricing': [
                {
                    'default': True,
                    'price_model': 'fixed_price',
                    'price_in_cogs': 1
                }
            ],
            'endpoints': [
                'http://node1.naint.tech:62400'
            ],
            'group_id': '/mb90Qs8VktxGQmU0uRu0bSlGgqeDlYrKrs+WbsOvOQ=',
            'group_name': 'default_group',
            'payment': {
                'payment_address': '0x0709e9B78756B740ab0C64427f43f8305fD6D1A7',
                'payment_expiration_threshold': 40320,
                'payment_channel_storage_type': 'etcd',
                'payment_channel_storage_client': {
                    'endpoints': [
                        'https://127.0.0.1:2379'
                    ],
                    'request_timeout': '3s',
                    'connection_timeout': '5s'
                }
            }
        }
        self.mock_service_stub = MagicMock()
        self.mock_payment_strategy = MagicMock()
        self.mock_options = {
            'free_call_auth_token-bin': '',
            'free-call-token-expiry-block': 0,
            'email': '',
            'concurrency': False,
            "endpoint": "http://localhost:5000"
        }
        self.mock_mpe_contract = MagicMock(spec=MPEContract)
        self.mock_mpe_contract.contract = MagicMock()
        self.mock_account = MagicMock(spec=Account)
        self.mock_account.signer_private_key = MagicMock()
        self.mock_sdk_web3 = MagicMock(spec=Web3)
        self.mock_sdk_web3.eth = MagicMock()
        self.mock_pb2_module = MagicMock()
        self.mock_payment_channel_provider = MagicMock(
            spec=PaymentChannelProvider
        )
        self.mock_path_to_pb_files = MagicMock(spec=Path)

        self.client = ServiceClient(
            self.mock_org_id,
            self.mock_service_id,
            self.mock_service_metadata,
            self.mock_group,
            self.mock_service_stub,
            self.mock_payment_strategy,
            self.mock_options,
            self.mock_mpe_contract,
            self.mock_account,
            self.mock_sdk_web3,
            self.mock_pb2_module,
            self.mock_payment_channel_provider,
            self.mock_path_to_pb_files
        )

    def test_call_rpc(self):
        # Set up mocks for service and pb2_module
        mock_rpc_method = MagicMock(return_value="value: 8")
        self.client.service = MagicMock()
        self.client.service.mul = mock_rpc_method
        self.mock_pb2_module.Numbers = MagicMock()

        # Call the method
        result = self.client.call_rpc("mul", "Numbers", a=2, b=4)

        # Assert that Numbers was called with correct arguments
        self.mock_pb2_module.Numbers.assert_called_once_with(a=2, b=4)
        mock_rpc_method.assert_called_once_with(
            self.mock_pb2_module.Numbers.return_value
        )
        self.assertEqual(result, mock_rpc_method.return_value)

    @patch("snet.sdk.service_client.grpc.insecure_channel")
    def test_get_grpc_channel_http(self, mock_insecure_channel):
        channel = self.client._get_grpc_channel()
        mock_insecure_channel.assert_called_once_with("localhost:5000")
        self.assertEqual(channel, mock_insecure_channel.return_value)

    @patch("snet.sdk.service_client.grpc.ssl_channel_credentials")
    @patch("snet.sdk.service_client.grpc.secure_channel")
    def test_get_grpc_channel_https(self,
                                    mock_secure_channel,
                                    mock_ssl_channel_credentials):
        self.mock_options["endpoint"] = "https://localhost:5000"
        channel = self.client._get_grpc_channel()
        mock_ssl_channel_credentials.assert_called_once()
        mock_secure_channel.assert_called_once_with(
            "localhost:5000",
            mock_ssl_channel_credentials.return_value
        )
        self.assertEqual(channel, mock_secure_channel.return_value)

    def test_filter_existing_channels(self):
        mock_existing_channel = MagicMock(channel_id=1)
        mock_new_channel_1 = MagicMock(channel_id=2)
        mock_new_channel_2 = MagicMock(channel_id=3)
        self.client.payment_channels = [mock_existing_channel]
        result = self.client._filter_existing_channels_from_new_payment_channels(   # noqa E501
            [mock_existing_channel, mock_new_channel_1, mock_new_channel_2]
        )
        self.assertEqual(result, [mock_new_channel_1, mock_new_channel_2])

    def test_get_current_block_number(self):
        expected_result = Mock(return_value=12345)
        self.client.sdk_web3.eth.block_number = expected_result
        result = self.client.get_current_block_number()
        self.assertEqual(result, expected_result)

    def test_generate_signature(self):
        message = b"test_message"
        mock_signature = MagicMock()
        self.client.sdk_web3.eth.account.signHash = MagicMock(
            return_value=MagicMock(signature=mock_signature)
        )
        result = self.client.generate_signature(message)
        self.assertEqual(result, bytes(mock_signature))

    @patch("snet.sdk.service_client.web3.Web3.solidity_keccak")
    def test_generate_training_signature(self, mock_solidity_keccak):
        text = "test_text"
        address = "test_address"
        block_number = "test_block_number"
        mock_solidity_keccak.return_value = b"test_message"
        mock_signature = MagicMock()
        self.client.sdk_web3.eth.account.signHash = MagicMock(
            return_value=MagicMock(signature=mock_signature)
        )
        result = self.client.generate_training_signature(text, address,
                                                         block_number)
        self.assertEqual(result, mock_signature)


if __name__ == "__main__":
    unittest.main()
