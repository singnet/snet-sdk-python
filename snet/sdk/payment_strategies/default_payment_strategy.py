from snet.sdk.payment_strategies.freecall_payment_strategy import FreeCallPaymentStrategy
from snet.sdk.payment_strategies.paidcall_payment_strategy import PaidCallPaymentStrategy
from snet.sdk.payment_strategies.prepaid_payment_strategy import PrePaidPaymentStrategy
from snet.sdk.payment_strategies.payment_strategy import PaymentStrategy


class DefaultPaymentStrategy(PaymentStrategy):

    def __init__(self):
        self.channel = None

    def set_channel(self, channel):
        self.channel = channel

    def get_payment_metadata(self, service_client):
        free_call_payment_strategy = FreeCallPaymentStrategy()

        if free_call_payment_strategy.get_free_calls_available(service_client) > 0:
            metadata = free_call_payment_strategy.get_payment_metadata(service_client)
        else:
            if service_client.get_concurrency_flag():
                concurrent_calls = service_client.get_concurrent_calls()
                payment_strategy = PrePaidPaymentStrategy(concurrent_calls)
                metadata = payment_strategy.get_payment_metadata(service_client)
            else:
                payment_strategy = PaidCallPaymentStrategy()
                metadata = payment_strategy.get_payment_metadata(service_client)

        return metadata

    def get_price(self, service_client):
        pass

    def get_concurrency_token_and_channel(self, service_client):
        concurrent_calls = service_client.get_concurrent_calls()
        payment_strategy = PrePaidPaymentStrategy(concurrent_calls)
        return payment_strategy.get_concurrency_token_and_channel(service_client)
