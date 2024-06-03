import unittest

from snet import sdk


class TestSDKClient(unittest.TestCase):
   def setUp(self):
       self.service_client = get_service_client()

    # TODO update/replace/remove tests that are commented out

    # def test_verify_when_no_open_channel(self):
    #     channels = self.service_client.load_open_channels()
    #     self.assertEqual(0, len(channels))

    def test_make_first_free_call(self):
        result = self.service_client.call_rpc("mul", "Numbers", a=20, b=4)
        self.assertEqual(80.0, result.value)

    # def test_make_second_free_call(self):
    #     result = self.service_client.call_rpc("mul", "Numbers", a=20, b=5)
    #     self.assertEqual(100.0, result.value)

    # def test_open_first_channel(self):
    #     channel = self.service_client.open_channel(123456, 33333)
    #     self.assertEqual(0, channel.channel_id)
    #     self.assertEqual(0, channel.state['nonce'])
    #     self.assertEqual(0, channel.state['last_signed_amount'])

    # def test_first_call_to_service_after_opening_first_channel(self):
    #     result = self.service_client.call_rpc("mul", "Numbers", a=20, b=3)
    #     self.assertEqual(60.0, result.value)

    # def test_verify_channel_state_after_opening_first_channel_and_first_call_to_service(self):
    #     self.service_client.update_channel_states()
    #     channels = self.service_client.load_open_channels()
    #     self.assertEqual(0, channels[0].channel_id)
    #     self.assertEqual(0, channels[0].state['nonce'])
    #     self.assertEqual(1000, channels[0].state['last_signed_amount'])

    # def test_second_call_to_service_after_opening_first_channel(self):
    #     result = self.service_client.call_rpc("mul", "Numbers", a=20, b=3)
    #     self.assertEqual(60.0, result.value)

    # def test_verify_channel_state_after_opening_first_channel_and_second_call_to_service(self):
    #     self.service_client.update_channel_states()
    #     channels = self.service_client.load_open_channels()
    #     self.assertEqual(0, channels[0].channel_id)
    #     self.assertEqual(0, channels[0].state['nonce'])
    #     self.assertEqual(2000, channels[0].state['last_signed_amount'])

    # def test_open_second_channel(self):
    #     channel = self.service_client.open_channel(1234321, 123456)
    #     self.assertEqual(1, channel.channel_id)
    #     self.assertEqual(0, channel.state['nonce'])
    #     self.assertEqual(0, channel.state['last_signed_amount'])

    # def test_verify_number_of_channel_after_opening_second_channel(self):
    #     self.service_client.update_channel_states()
    #     channels = self.service_client.load_open_channels()
    #     self.assertEqual(0, channels[0].channel_id)
    #     self.assertEqual(0, channels[0].state['nonce'])
    #     self.assertEqual(2000, channels[0].state['last_signed_amount'])
    #     self.assertEqual(1, channels[1].channel_id)
    #     self.assertEqual(0, channels[1].state['nonce'])
    #     self.assertEqual(0, channels[1].state['last_signed_amount'])

    # def test_first_call_to_service_after_opening_second_channel(self):
    #     result = self.service_client.call_rpc("mul", "Numbers", a=20, b=3)
    #     self.assertEqual(60.0, result.value)

    # def test_verify_channel_state_after_opening_second_channel_and_first_call_to_service(self):
    #     self.service_client.update_channel_states()
    #     channels = self.service_client.load_open_channels()
    #     self.assertEqual(0, channels[0].channel_id)
    #     self.assertEqual(0, channels[0].state['nonce'])
    #     self.assertEqual(3000, channels[0].state['last_signed_amount'])
    #     self.assertEqual(1, channels[1].channel_id)
    #     self.assertEqual(0, channels[1].state['nonce'])
    #     self.assertEqual(0, channels[1].state['last_signed_amount'])


def get_service_client():
    org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
    service_id = "Exampleservice"
    group_name = "default_group"

    # TODO remove test keys from repo
    config = {
        #"private_key": "51ec611f164a078a13dba33e5afefcd62c8460545b2d48177a27443971482b4a",
        "private_key": "59a9eddfd4d043890ed79a8475a9b7ebda8a76857d88363e01b1b9c5f2ea68c5",
        "eth_rpc_endpoint": "https://sepolia.infura.io/v3/09027f4a13e841d48dbfefc67e7685d5",
        "email": "test@test.com",
        # "free_call_auth_token-bin":"f5533eb0f01f0d45239c11b411bdfd4221fd3b125e4250db1f7bc044466108bc10ce95ab62ae224b6578b68d0ce337b4ec36e4b9dfbe6653e04973107813cbc01c",
        # "free-call-token-expiry-block":19690819,
        "concurrency": False,
        "org_id": org_id,
        "service_id": service_id,
        "identity_name": "test",
        "identity_type": "key",
    }

    snet_sdk = sdk.SnetSDK(config)
    service_client = snet_sdk.create_service_client(org_id, service_id, group_name)
    return service_client


if __name__ == '__main__':
    unittest.main()
