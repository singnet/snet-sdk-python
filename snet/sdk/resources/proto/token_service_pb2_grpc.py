# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import token_service_pb2 as token__service__pb2


class TokenServiceStub(object):
    """It is expected that the user would call the GetChannelState to Determine the Current state of the Channel
    Based on the usage forecast, the user/client will have to sign for an amount L + U , where L is the last amount Signed
    and U is the amount based on expected usage.
    Please be aware that the Signing up an amount upfront ( Pre Paid) does come with a risk and hence the
    user must exercise caution on the amount signed specially with new service providers.
    If there is no need of making concurrent calls then you may consider pay per mode.
    Using a Token, the Client can now make concurrent calls, which was not supported previously with the pay per mode.
    However the pay per mode is a lot secure than the pre-paid mode.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetToken = channel.unary_unary(
                '/escrow.TokenService/GetToken',
                request_serializer=token__service__pb2.TokenRequest.SerializeToString,
                response_deserializer=token__service__pb2.TokenReply.FromString,
                )


class TokenServiceServicer(object):
    """It is expected that the user would call the GetChannelState to Determine the Current state of the Channel
    Based on the usage forecast, the user/client will have to sign for an amount L + U , where L is the last amount Signed
    and U is the amount based on expected usage.
    Please be aware that the Signing up an amount upfront ( Pre Paid) does come with a risk and hence the
    user must exercise caution on the amount signed specially with new service providers.
    If there is no need of making concurrent calls then you may consider pay per mode.
    Using a Token, the Client can now make concurrent calls, which was not supported previously with the pay per mode.
    However the pay per mode is a lot secure than the pre-paid mode.
    """

    def GetToken(self, request, context):
        """GetToken method checks the Signature sent and returns a Token
        1) The Signature is valid and has to be signed in the below format
        "__MPE_claim_message"+MpeContractAddress+ChannelID+ChannelNonce+SignedAmount
        Signature is to let the Service Provider make a claim
        2) Signed amount >= Last amount Signed.
        if Signed amount == Last Signed amount , then check if planned_amount < used_amount
        if Signed amount > Last Signed amount , then update the planned amount = Signed Amount
        GetToken method in a way behaves as a renew Token too!.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TokenServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetToken': grpc.unary_unary_rpc_method_handler(
                    servicer.GetToken,
                    request_deserializer=token__service__pb2.TokenRequest.FromString,
                    response_serializer=token__service__pb2.TokenReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'escrow.TokenService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class TokenService(object):
    """It is expected that the user would call the GetChannelState to Determine the Current state of the Channel
    Based on the usage forecast, the user/client will have to sign for an amount L + U , where L is the last amount Signed
    and U is the amount based on expected usage.
    Please be aware that the Signing up an amount upfront ( Pre Paid) does come with a risk and hence the
    user must exercise caution on the amount signed specially with new service providers.
    If there is no need of making concurrent calls then you may consider pay per mode.
    Using a Token, the Client can now make concurrent calls, which was not supported previously with the pay per mode.
    However the pay per mode is a lot secure than the pre-paid mode.
    """

    @staticmethod
    def GetToken(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/escrow.TokenService/GetToken',
            token__service__pb2.TokenRequest.SerializeToString,
            token__service__pb2.TokenReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
