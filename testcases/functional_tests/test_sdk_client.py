import unittest
import os

from snet import sdk
from snet.sdk import PaymentStrategyType


class TestSDKClient(unittest.TestCase):
    def setUp(self):
        self.service_client = get_test_service_data()

    def test_call_to_service(self):
        result = self.service_client.call_rpc("mul", "Numbers", a=20, b=3)
        self.assertEqual(60.0, result.value)


def get_test_service_data():
    config = sdk.config.Config(private_key=os.environ['SNET_TEST_WALLET_PRIVATE_KEY'],
                               eth_rpc_endpoint=f"https://sepolia.infura.io/v3/{os.environ['SNET_TEST_INFURA_KEY']}",
                               concurrency=False)

    snet_sdk = sdk.SnetSDK(config)
    
    service_client = snet_sdk.create_service_client(org_id="26072b8b6a0e448180f8c0e702ab6d2f",
                                                    service_id="Exampleservice", group_name="default_group",
                                                    payment_strategy_type=PaymentStrategyType.PAID_CALL)
    return service_client


if __name__ == '__main__':
    unittest.main()
