import unittest

from snet.sdk.config import Config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.private_key = "test_private_key"
        self.eth_rpc_endpoint = "http://localhost:8545"
        self.wallet_index = 1
        self.ipfs_endpoint = "http://custom-ipfs-endpoint.io"
        self.mpe_contract_address = "0xMPEAddress"
        self.token_contract_address = "0xTokenAddress"
        self.registry_contract_address = "0xRegistryAddress"
        self.signer_private_key = "signer_key"

    def test_initialization(self):
        config = Config(
            private_key=self.private_key,
            eth_rpc_endpoint=self.eth_rpc_endpoint,
            wallet_index=self.wallet_index,
            ipfs_endpoint=self.ipfs_endpoint,
            concurrency=False,
            force_update=True,
            mpe_contract_address=self.mpe_contract_address,
            token_contract_address=self.token_contract_address,
            registry_contract_address=self.registry_contract_address,
            signer_private_key=self.signer_private_key
        )

        self.assertEqual(config["private_key"],
                         self.private_key)
        self.assertEqual(config["eth_rpc_endpoint"],
                         self.eth_rpc_endpoint)
        self.assertEqual(config["wallet_index"],
                         self.wallet_index)
        self.assertEqual(config["ipfs_endpoint"],
                         self.ipfs_endpoint)
        self.assertEqual(config["mpe_contract_address"],
                         self.mpe_contract_address)
        self.assertEqual(config["token_contract_address"],
                         self.token_contract_address)
        self.assertEqual(config["registry_contract_address"],
                         self.registry_contract_address)
        self.assertEqual(config["signer_private_key"],
                         self.signer_private_key)
        self.assertEqual(config["lighthouse_token"], " ")
        self.assertFalse(config["concurrency"])
        self.assertTrue(config["force_update"])

    def test_default_values(self):
        config = Config(
            private_key=self.private_key,
            eth_rpc_endpoint=self.eth_rpc_endpoint
        )

        self.assertEqual(config["wallet_index"], 0)
        self.assertEqual(config["ipfs_endpoint"],
                         "/dns/ipfs.singularitynet.io/tcp/80/")
        self.assertTrue(config["concurrency"])
        self.assertFalse(config["force_update"])
        self.assertIsNone(config["mpe_contract_address"])
        self.assertIsNone(config["token_contract_address"])
        self.assertIsNone(config["registry_contract_address"])
        self.assertIsNone(config["signer_private_key"])

    def test_get_method(self):
        config = Config(private_key=self.private_key,
                        eth_rpc_endpoint=self.eth_rpc_endpoint)

        self.assertEqual(config.get("private_key"), self.private_key)
        self.assertEqual(config.get("non_existent_key",
                                    "default_value"), "default_value")
        self.assertIsNone(config.get("non_existent_key"))

    def test_get_ipfs_endpoint(self):
        config = Config(private_key=self.private_key,
                        eth_rpc_endpoint=self.eth_rpc_endpoint)
        self.assertEqual(config.get_ipfs_endpoint(),
                         "/dns/ipfs.singularitynet.io/tcp/80/")

        config_with_custom_ipfs = Config(
            private_key=self.private_key,
            eth_rpc_endpoint=self.eth_rpc_endpoint,
            ipfs_endpoint=self.ipfs_endpoint
        )
        self.assertEqual(config_with_custom_ipfs.get_ipfs_endpoint(),
                         self.ipfs_endpoint)


if __name__ == "__main__":
    unittest.main()
