# Welcome to snet-sdk-python's documentation!

SingularityNET SDK for Python

### Core concepts

The SingularityNET SDK allows you to make calls to SingularityNET services programmatically from your application.
To communicate between clients and services, SingularityNET uses [gRPC](https://grpc.io/).
To handle payment of services, SingularityNET uses [Ethereum state channels](https://dev.singularitynet.io/docs/concepts/multi-party-escrow/).
The SingularityNET SDK abstracts and manages state channels with service providers on behalf of the user and handles authentication with the SingularityNET services.

A getting started guide for the SNET SDK for Python is available [here](https://github.com/singnet/snet-sdk-python/blob/master/README.md).

### Package Diagram

![Package Diagram]()

### Modules

1. metadata_provider
   1. [metadata_provider](metadata_provider/metadata_provider.md)
   2. [ipfs_metadata_provider](metadata_provider/ipfs_metadata_provider.md)
2. mpe
   1. [mpe_contract](mpe/mpe_contract.md)
   2. [payment_channel](mpe/payment_channel.md)
   3. [payment_channel_provider](mpe/payment_channel_provider.md)
3. payment_strategies
   1. [payment_strategy](payment_strategies/payment_strategy.md)
   2. [default_payment_strategy]()
   3. [freecall_payment_strategy]()
   4. [paidcall_payment_strategy]()
   5. [prepaid_payment_strategy]()
4. training
   1. [training](training/training.md)
5. [init](main/init.md)
6. [account](main/account.md)
7. [service_client](main/service_client.md)
8. [concurrency_manager](main/concurrency_manager.md)
9. [generic_client_interceptor](main/generic_client_interceptor.md)

