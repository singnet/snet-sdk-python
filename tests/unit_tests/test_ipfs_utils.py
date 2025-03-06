import unittest
from unittest.mock import MagicMock, patch

import ipfshttpclient

from snet.sdk.config import Config
from snet.sdk.utils.ipfs_utils import (get_from_ipfs_and_checkhash,
                                       get_ipfs_client)


class TestIpfsUtils(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=ipfshttpclient.Client)
        self.hash_base58 = "QmTestHashBase58"
        self.valid_data = b"test data"
        self.block_data = b"block data"
        self.ipfs_endpoint = "http://127.0.0.1:5001"

        self.mock_client.cat.return_value = self.valid_data
        self.mock_client.block.get.return_value = self.block_data

    @patch("snet.sdk.utils.ipfs_utils.multihash")
    def test_get_from_ipfs_and_checkhash_with_verify_success(
        self, mock_multihash
    ):
        # Mock multihash behavior
        mock_mh_instance = MagicMock()
        mock_multihash.decode.return_value = mock_mh_instance
        mock_mh_instance.verify.return_value = True

        # Call the function
        result = get_from_ipfs_and_checkhash(self.mock_client,
                                             self.hash_base58,
                                             validate=True)

        # Assertions
        self.assertEqual(result, self.valid_data)
        self.mock_client.cat.assert_called_once_with(self.hash_base58)
        self.mock_client.block.get.assert_called_once_with(self.hash_base58)
        mock_multihash.decode.assert_called_once_with(
            self.hash_base58.encode('ascii'), "base58"
        )
        mock_mh_instance.verify.assert_called_once_with(self.block_data)

    @patch("snet.sdk.utils.ipfs_utils.multihash")
    def test_get_from_ipfs_and_checkhash_with_verify_failure(
        self, mock_multihash
    ):
        # Mock multihash behavior
        mock_mh_instance = MagicMock()
        mock_multihash.decode.return_value = mock_mh_instance
        mock_mh_instance.verify.return_value = False

        # Call the function and expect an exception
        with self.assertRaises(Exception) as context:
            get_from_ipfs_and_checkhash(self.mock_client,
                                        self.hash_base58,
                                        validate=True)
        self.assertEqual(str(context.exception),
                         "IPFS hash mismatch with data")

    @patch("snet.sdk.utils.ipfs_utils.multihash")
    def test_get_from_ipfs_and_checkhash_invalid_multihash(
        self, mock_multihash
    ):
        # Mock multihash behavior to raise an exception
        mock_multihash.decode.side_effect = ValueError("Invalid multihash")

        # Call the function and expect an exception
        with self.assertRaises(ValueError) as context:
            get_from_ipfs_and_checkhash(self.mock_client,
                                        self.hash_base58,
                                        validate=True)
        self.assertIn("Invalid multihash", str(context.exception))

    def test_get_from_ipfs_and_checkhash_without_validation(self):
        # Call the function
        result = get_from_ipfs_and_checkhash(self.mock_client,
                                             self.hash_base58,
                                             validate=False)

        # Assertions
        self.assertEqual(result, self.valid_data)
        self.mock_client.cat.assert_called_once_with(self.hash_base58)
        self.mock_client.block.get.assert_not_called()

    @patch("snet.sdk.utils.ipfs_utils.ipfshttpclient.connect")
    def test_get_ipfs_client(self, mock_connect):
        mock_config = MagicMock(spec=Config)
        mock_config.get_ipfs_endpoint.return_value = self.ipfs_endpoint

        # Call the function
        client = get_ipfs_client(mock_config)

        # Assertions
        mock_connect.assert_called_once_with(self.ipfs_endpoint)
        self.assertEqual(client, mock_connect.return_value)


if __name__ == "__main__":
    unittest.main()
