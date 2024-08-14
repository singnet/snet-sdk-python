## module: sdk.service_client.py

Entities:
1. [ServiceClient](#class-serviceclient)
   - [\_\_init\_\_](#init)
   - [call_rpc](#call_rpc)
   - [_generate_grpc_stub](#_generate_grpc_stub)
   - [get_grpc_base_channel](#get_grpc_base_channel)
   - [_get_grpc_channel](#_get_grpc_channel)
   - [_get_service_call_metadata](#_get_service_call_metadata)
   - [_intercept_call](#_intercept_call)
   - [_filter_existing_channels_from_new_payment_channels](#_filter_existing_channels_from_new_payment_channels)
   - [load_open_channels](#load_open_channels)
   - [get_current_block_number](#get_current_block_number)
   - [update_channel_states](#update_channel_states)
   - [default_channel_expiration](#default_channel_expiration)
   - [_generate_payment_channel_state_service_client](#_generate_payment_channel_state_service_client)
   - [open_channel](#open_channel)
   - [deposit_and_open_channel](#deposit_and_open_channel)
   - [get_price](#get_price)
   - [generate_signature](#generate_signature)
   - [generate_training_signature](#generate_training_signature)
   - [get_free_call_config](#get_free_call_config)
   - [get_service_details]()
   - [get_concurrency_flag]()
   - [get_concurrency_token_and_channel]()
   - [set_concurrency_token_and_channel]()
   - [get_path_to_pb_files]()
   - [get_services_and_messages_info]()
   - [get_services_and_messages_info_as_pretty_string]()

### class `ServiceClient`

extends: -

is extended by: -

#### description

This class is responsible for creating a client for interacting with a service. 
It initializes various attributes and sets up a gRPC channel for communication with the service. 
The class is used to manage the communication and payment channel management for a service in the SDK.

#### attributes

- `org_id` (str): The organization id.
- `service_id` (str): The service id.
- `options` (dict): Additional options for the service client.
- `group` (dict): The payment group details.
- `service_metadata` (MPEServiceMetadata): An instance of the `MPEServiceMetadata` class with the metadata of 
the specified service.
- `payment_strategy` (PaymentStrategy): The payment strategy. _Note_: In fact, this is an instance of one of 
the "PaymentStrategy" inheritor classes. 
- `expiry_threshold` (int): The payment expiration threshold (in blocks).
- `__base_grpc_channel` (grpc.Channel): The base gRPC channel.
- `grpc_channel` (grpc.Channel): The gRPC channel with interceptor.
- `payment_channel_provider` (PaymentChannelProvider): An instance of the `PaymentChannelProvider` class for 
working with channels and interacting with MPE.
- `service` (Any): The gRPC service stub instance.
- `pb2_module` (ModuleType): The imported protobuf module.
- `payment_channels` (list[PaymentChannel]): The list of payment channels.
- `last_read_block` (int): The last read block number.
- `account` (Account): An instance of the `Account` class for interacting with the MultiPartyEscrow and 
SingularityNetToken contracts.
- `sdk_web3` (Web3): The Web3 instance.
- `mpe_address` (str): The MPE contract address.

#### methods

#### `__init__`

Initializes a new instance of the class.

###### args:

- `org_id` (str): The ID of the organization.
- `service_id` (str): The ID of the service.
- `service_metadata` (MPEServiceMetadata): The metadata for the service.
- `group` (dict): The payment group from the service metadata.
- `service_stub` (ServiceStub): The gRPC service stub.
- `payment_strategy` (PaymentStrategy): The payment channel management strategy.
- `options` (dict): Additional options for the service client.
- `mpe_contract` (MPEContract): The MPE contract instance.
- `account` (Account): An instance of the `Account` class.
- `sdk_web3` (Web3): The Web3 instance.
- `pb2_module` (Union[str, ModuleType]): The module containing the gRPC message definitions.

###### returns:

- _None_

#### `call_rpc`

Calls an RPC method on the service client and returns its result.

###### args:

- `rpc_name` (str): The name of the RPC method to call.
- `message_class` (str): The name of the message class to use for the request.
- `**kwargs`: Keyword arguments to pass to the message class constructor, in fact, these are the values 
that are passed to the called method as arguments.

###### returns:

- The response from the RPC method call. (Any)

#### `_generate_grpc_stub`

Generates a gRPC stub instance for the given service stub.

###### args:

- `service_stub` (ServiceStub): The gRPC service stub.

###### returns:

-  stub_instance (object): The generated gRPC stub instance.

#### `get_grpc_base_channel`

Returns the base gRPC channel used by the service client.

###### returns:

- `self.__base_grpc_channel` (grpc.Channel)

#### `_get_grpc_channel`

Returns a gRPC channel based on the provided endpoint. 

Retrieves the endpoint from the options dictionary or from the service metadata. If no endpoint is provided, 
it uses the first endpoint from the group specified in the service metadata. The endpoint is parsed using 
the `urlparse` function to extract the hostname and port. If a port is specified, it is concatenated with 
the hostname to form the channel endpoint. Otherwise, only the hostname is used as the channel endpoint. 
The scheme of the endpoint is used to determine the type of channel to be created. If the scheme is "http", 
an insecure channel is created using the channel endpoint. If the scheme is "https", a secure channel is 
created using the channel endpoint and the root certificates. If the scheme is neither "http" nor "https", 
a ValueError is raised with an error message.

###### returns:

- The gRPC channel based on the provided endpoint. (grpc.Channel)

###### raises:

- ValueError: If the scheme in the service metadata is neither "http" nor "https".

#### `_get_service_call_metadata`

Retrieves the metadata required for making a service call using the payment strategy.

###### returns:

- Payment metadata. (list[tuple[str, Any]])

#### `_intercept_call`



###### args:

- 

###### returns:

-  

#### `_filter_existing_channels_from_new_payment_channels`

Filters the new channel list so that only those that are not yet among the existing ones remain, 
and returns them as a list.

###### args:

- `new_payment_channels` (list[PaymentChannel]): A list of `PaymentChannel` objects representing the new 
payment channels to filter.

###### returns:

- A list of the new payment channels that are not already in the `self.payment_channels` list. (list[PaymentChannel])

#### `load_open_channels`

Load open payment channels and update the payment channels list. 

Retrieves open payment channels from the payment channel provider based on the current account, payment address, 
group ID, and last read block. It then filters out any existing channels from the new payment channels and 
updates the payment channels list with the new channels. Finally, it updates the last read block with the 
current block number and returns the updated payment channels list. 

###### returns:

- The updated payment channels list. (list[PaymentChannel])

#### `get_current_block_number`

Returns the current block number from the Ethereum blockchain using Web3.

###### returns:

- The current block number. (int)

#### `update_channel_states`

Updates the state of each channel in the `payment_channels` list.

###### returns:

- `self.payment_channels` with updated states. (list[PaymentChannel]) 

#### `default_channel_expiration`

Returns the default expiration time for the payment channel, calculated as the current block number 
plus the expiry threshold.

###### returns:

- The default expiration time for a payment channel (block number). (int)

#### `_generate_payment_channel_state_service_client`

Generates a payment channel state service client.

Creates a gRPC channel using the base channel and imports the necessary modules for the 
state service. It then uses the imported module to create a PaymentChannelStateServiceStub object, which 
is the client for the payment channel state service.

###### returns:

- Payment channel state service client stub. (Any)

#### `open_channel`

Opens a payment channel with the specified amount of AGIX tokens in cogs and expiration time.

###### args:

- `amount` (int): The amount of AGIX tokens in cogs to deposit into the channel.
- `expiration` (int): The expiration time of the payment channel in blocks.

###### returns:

- Newly opened payment channel. (PaymentChannel)

#### `deposit_and_open_channel`

Deposits the specified amount of tokens into the MPE smart contract and opens a payment channel 
with its amount of AGIX tokens in cogs and expiration time.

###### args:

- `amount` (int): The amount of AGIX tokens in cogs to deposit into the channel.
- `expiration` (int): The expiration time of the payment channel in blocks.

###### returns:

- Newly opened payment channel. (PaymentChannel)

#### `get_price`



###### args:

- 

###### returns:

- 

#### `generate_signature`



###### args:

- 

###### returns:

- 

#### `generate_training_signature`



###### args:

- 

###### returns:

- 

#### `get_free_call_config`



###### args:

- 

###### returns:

- 
