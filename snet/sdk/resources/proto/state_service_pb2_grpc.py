# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import state_service_pb2 as state__service__pb2


class PaymentChannelStateServiceStub(object):
    """PaymentChannelStateService contains methods to get the MultiPartyEscrow
    payment channel state.
    channel_id, channel_nonce, value and amount fields below in fact are
    Solidity uint256 values. Which are big-endian integers, see
    https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#formal-specification-of-the-encoding
    These values may be or may be not padded by zeros, service supports both
    options.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetChannelState = channel.unary_unary(
                '/escrow.PaymentChannelStateService/GetChannelState',
                request_serializer=state__service__pb2.ChannelStateRequest.SerializeToString,
                response_deserializer=state__service__pb2.ChannelStateReply.FromString,
                )


class PaymentChannelStateServiceServicer(object):
    """PaymentChannelStateService contains methods to get the MultiPartyEscrow
    payment channel state.
    channel_id, channel_nonce, value and amount fields below in fact are
    Solidity uint256 values. Which are big-endian integers, see
    https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#formal-specification-of-the-encoding
    These values may be or may be not padded by zeros, service supports both
    options.
    """

    def GetChannelState(self, request, context):
        """GetChannelState method returns a channel state by channel id.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PaymentChannelStateServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetChannelState': grpc.unary_unary_rpc_method_handler(
                    servicer.GetChannelState,
                    request_deserializer=state__service__pb2.ChannelStateRequest.FromString,
                    response_serializer=state__service__pb2.ChannelStateReply.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'escrow.PaymentChannelStateService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class PaymentChannelStateService(object):
    """PaymentChannelStateService contains methods to get the MultiPartyEscrow
    payment channel state.
    channel_id, channel_nonce, value and amount fields below in fact are
    Solidity uint256 values. Which are big-endian integers, see
    https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#formal-specification-of-the-encoding
    These values may be or may be not padded by zeros, service supports both
    options.
    """

    @staticmethod
    def GetChannelState(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/escrow.PaymentChannelStateService/GetChannelState',
            state__service__pb2.ChannelStateRequest.SerializeToString,
            state__service__pb2.ChannelStateReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class FreeCallStateServiceStub(object):
    """Used to determine free calls available for a given user.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetFreeCallsAvailable = channel.unary_unary(
                '/escrow.FreeCallStateService/GetFreeCallsAvailable',
                request_serializer=state__service__pb2.FreeCallStateRequest.SerializeToString,
                response_deserializer=state__service__pb2.FreeCallStateReply.FromString,
                )
        self.GetFreeCallToken = channel.unary_unary(
                '/escrow.FreeCallStateService/GetFreeCallToken',
                request_serializer=state__service__pb2.GetFreeCallTokenRequest.SerializeToString,
                response_deserializer=state__service__pb2.FreeCallToken.FromString,
                )


class FreeCallStateServiceServicer(object):
    """Used to determine free calls available for a given user.
    """

    def GetFreeCallsAvailable(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetFreeCallToken(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_FreeCallStateServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetFreeCallsAvailable': grpc.unary_unary_rpc_method_handler(
                    servicer.GetFreeCallsAvailable,
                    request_deserializer=state__service__pb2.FreeCallStateRequest.FromString,
                    response_serializer=state__service__pb2.FreeCallStateReply.SerializeToString,
            ),
            'GetFreeCallToken': grpc.unary_unary_rpc_method_handler(
                    servicer.GetFreeCallToken,
                    request_deserializer=state__service__pb2.GetFreeCallTokenRequest.FromString,
                    response_serializer=state__service__pb2.FreeCallToken.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'escrow.FreeCallStateService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class FreeCallStateService(object):
    """Used to determine free calls available for a given user.
    """

    @staticmethod
    def GetFreeCallsAvailable(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/escrow.FreeCallStateService/GetFreeCallsAvailable',
            state__service__pb2.FreeCallStateRequest.SerializeToString,
            state__service__pb2.FreeCallStateReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetFreeCallToken(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/escrow.FreeCallStateService/GetFreeCallToken',
            state__service__pb2.GetFreeCallTokenRequest.SerializeToString,
            state__service__pb2.FreeCallToken.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
