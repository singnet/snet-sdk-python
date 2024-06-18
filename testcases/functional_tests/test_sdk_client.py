import unittest
import shutil
import os

from snet import sdk


class TestSDKClient(unittest.TestCase):
    def setUp(self):
        self.service_client, self.path_to_pb_files = get_test_service_data()
        channel = self.service_client.open_channel(123456, 33333)

    def test__call_to_service(self):
        result = self.service_client.call_rpc("mul", "Numbers", a=20, b=3)
        self.assertEqual(60.0, result.value)

    def tearDown(self):
        try:
            shutil.rmtree(self.path_to_pb_files)
            print(f"Directory '{self.path_to_pb_files}' has been removed successfully after testing.")
        except OSError as e:
            print(f"Error: {self.path_to_pb_files} : {e.strerror}")


def get_test_service_data():
    org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
    service_id = "Exampleservice"
    group_name = "default_group"

    config = {
        "private_key": os.environ['SNET_TEST_WALLET_PRIVATE_KEY'],
        "eth_rpc_endpoint": f"https://sepolia.infura.io/v3/{os.environ['SNET_TEST_INFURA_KEY']}",
        "email": "test@test.com",
        "concurrency": False,
        "org_id": org_id,
        "service_id": service_id,
        "identity_name": "test",
        "identity_type": "key",
        "network": "sepolia",
        "force_update": False
    }

    snet_sdk = sdk.SnetSDK(config)
    service_client = snet_sdk.create_service_client(org_id, service_id, group_name)
    path_to_pb_files = snet_sdk.get_path_to_pb_files(org_id, service_id)
    return service_client, path_to_pb_files


if __name__ == '__main__':
    unittest.main()
