import web3

from snet.sdk.payment_strategies.paidcall_payment_strategy import PaidCallPaymentStrategy


class TrainingPaymentStrategy(PaidCallPaymentStrategy):
    def __init__(self):
        super().__init__()
        self._call_price = -1
        self._train_model_id = ""

    def get_price(self, service_client=None) -> int:
        if self._call_price == -1:
            raise Exception("Training call price not set")
        return self._call_price

    def set_price(self, call_price: int) -> None:
        self._call_price = call_price

    def get_model_id(self):
        return self._train_model_id

    def set_model_id(self, model_id: str):
        self._train_model_id = model_id

    def get_payment_metadata(self, service_client) -> list[tuple[str, str]]:
        channel = self.select_channel(service_client)
        amount = channel.state["last_signed_amount"] + int(self.get_price(service_client))
        message = web3.Web3.solidity_keccak(
            ["string", "address", "uint256", "uint256", "uint256"],
            ["__MPE_claim_message", service_client.mpe_address, channel.channel_id,
             channel.state["nonce"],
             amount]
        )
        signature = service_client.generate_signature(message)

        metadata = [
            ("snet-payment-type", "train-call"),
            ("snet-payment-channel-id", str(channel.channel_id)),
            ("snet-payment-channel-nonce", str(channel.state["nonce"])),
            ("snet-payment-channel-amount", str(amount)),
            ("snet-train-model-id", self.get_model_id()),
            ("snet-payment-channel-signature-bin", signature)
        ]

        return metadata
