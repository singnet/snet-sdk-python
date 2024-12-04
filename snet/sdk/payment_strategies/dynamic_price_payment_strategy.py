from snet.sdk.payment_strategies.paidcall_payment_strategy import PaidCallPaymentStrategy


class DynamicPricePaymentStrategy(PaidCallPaymentStrategy):
    def __init__(self):
        super().__init__()
        self._call_price = -1

    def get_price(self, service_client=None):
        if self._call_price == -1:
            raise Exception("Training call price not set")
        return self._call_price

    def set_price(self, call_price: int):
        self._call_price = call_price
