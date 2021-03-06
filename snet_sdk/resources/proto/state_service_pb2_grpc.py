# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import state_service_pb2 as state__service__pb2


class PaymentChannelStateServiceStub(object):
  """PaymentChannelStateService contains methods to get the MultiPartyEscrow
  payment channel state.
  channel_id, channel_nonce, value and amount fields below in fact are
  Solidity uint256 values. Which are big-endian integers padded by zeros, see
  https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#formal-specification-of-the-encoding
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
  Solidity uint256 values. Which are big-endian integers padded by zeros, see
  https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#formal-specification-of-the-encoding
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
