from snet import sdk
from snet.sdk.service_client import ServiceClient


def verify_when_no_open_channel(service_client: ServiceClient):
    channels = service_client.load_open_channels()
    assert len(channels) == 0


def make_first_free_call(service_client: ServiceClient):
    result = service_client.call_rpc("mul", "Numbers", a=20, b=4)
    assert result.value == 80.0


def make_second_free_call(service_client: ServiceClient):
    result = service_client.call_rpc("mul", "Numbers", a=20, b=5)
    assert result.value == 100.0


def open_first_channel(service_client: ServiceClient):
    channel = service_client.open_channel(123456, 33333)
    assert channel.channel_id == 0
    assert channel.state['nonce'] == 0
    assert channel.state['last_signed_amount'] == 0


def first_call_to_service_after_opening_first_channel(service_client: ServiceClient):
    result = service_client.call_rpc("mul", "Numbers", a=20, b=3)
    assert result.value == 60.0


def verify_channel_state_after_opening_first_channel_and_first_call_to_service(service_client: ServiceClient):
    service_client.update_channel_states()
    channels = service_client.load_open_channels()
    assert channels[0].channel_id == 0
    assert channels[0].state['nonce'] == 0
    assert channels[0].state['last_signed_amount'] == 1000


def second_call_to_service_after_opening_first_channel(service_client: ServiceClient):
    result = service_client.call_rpc("mul", "Numbers", a=20, b=3)
    assert result.value == 60.0


def verify_channel_state_after_opening_first_channel_and_second_call_to_service(service_client: ServiceClient):
    service_client.update_channel_states()
    channels = service_client.load_open_channels()
    assert channels[0].channel_id == 0
    assert channels[0].state['nonce'] == 0
    assert channels[0].state['last_signed_amount'] == 2000


def open_second_channel(service_client: ServiceClient):
    channel = service_client.open_channel(1234321, 123456)
    assert channel.channel_id == 1
    assert channel.state['nonce'] == 0
    assert channel.state['last_signed_amount'] == 0


def verify_number_of_channel_after_opening_second_channel(service_client: ServiceClient):
    service_client.update_channel_states()
    channels = service_client.load_open_channels()
    assert channels[0].channel_id == 0
    assert channels[0].state['nonce'] == 0
    assert channels[0].state['last_signed_amount'] == 2000
    assert channels[1].channel_id == 1
    assert channels[1].state['nonce'] == 0
    assert channels[1].state['last_signed_amount'] == 0


def first_call_to_service_after_opening_second_channel(service_client: ServiceClient):
    result = service_client.call_rpc("mul", "Numbers", a=20, b=3)
    assert result.value == 60.0


def verify_channel_state_after_opening_second_channel_and_first_call_to_service(service_client: ServiceClient):
    service_client.update_channel_states()
    channels = service_client.load_open_channels()
    assert channels[0].channel_id == 0
    assert channels[0].state['nonce'] == 0
    assert channels[0].state['last_signed_amount'] == 3000
    assert channels[1].channel_id == 1
    assert channels[1].state['nonce'] == 0
    assert channels[1].state['last_signed_amount'] == 0


def test_sdk():
    org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
    service_id = "Exampleservice"
    group_name="default_group"

    config = {
        "private_key": "51ec611f164a078a13dba33e5afefcd62c8460545b2d48177a27443971482b4a",
        "eth_rpc_endpoint": "https://sepolia.infura.io/v3/09027f4a13e841d48dbfefc67e7685d5",
        "email":"test@test.com",
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


    make_first_free_call(service_client)
    make_second_free_call(service_client)
    verify_when_no_open_channel(service_client)
    open_first_channel(service_client)
    first_call_to_service_after_opening_first_channel(service_client)
    verify_channel_state_after_opening_first_channel_and_first_call_to_service(service_client)
    second_call_to_service_after_opening_first_channel(service_client)
    verify_channel_state_after_opening_first_channel_and_second_call_to_service(service_client)
    open_second_channel(service_client)
    verify_number_of_channel_after_opening_second_channel(service_client)
    first_call_to_service_after_opening_second_channel(service_client)
    verify_channel_state_after_opening_second_channel_and_first_call_to_service(service_client)


if __name__ == '__main__':
    test_sdk()
