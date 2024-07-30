# snet-sdk-python
  
SingularityNET SDK for Python

## Package

The package is published in PyPI at the following link:

|Package                                       |Description                                                          |
|----------------------------------------------|---------------------------------------------------------------------|
|[snet.sdk](https://pypi.org/project/snet.sdk/)|Integrate SingularityNET services seamlessly into Python applications|

## Getting Started  
  
These instructions are for the development and use of the SingularityNET SDK for Python.

### Core concepts

The SingularityNET SDK allows you to make calls to SingularityNET services programmatically from your application.
To communicate between clients and services, SingularityNET uses [gRPC](https://grpc.io/).
To handle payment of services, SingularityNET uses [Ethereum state channels](https://dev.singularitynet.io/docs/concepts/multi-party-escrow/).
The SingularityNET SDK abstracts and manages state channels with service providers on behalf of the user and handles authentication with the SingularityNET services.

### Usage

To call a SingularityNET service, the user must be able to deposit funds (AGIX tokens) to the [Multi-Party Escrow](https://dev.singularitynet.io/docs/concepts/multi-party-escrow/) Smart Contract.
To deposit these tokens or do any other transaction on the Ethereum blockchain, the user must possess an Ethereum identity with available Ether.

Once you have installed snet-sdk in your current environment, you can import it into your Python script and create an instance of the base sdk class:
```python
from snet import sdk
config = {
        "private_key": 'YOUR_PRIVATE_WALLET_KEY',
        "eth_rpc_endpoint": f"https://sepolia.infura.io/v3/YOUR_INFURA_KEY",
        "email": "your@email.com",
        "concurrency": False,
        "identity_name": "local_name_for_that_identity",
        "identity_type": "key",
        "network": "sepolia",
        "force_update": False
    }

snet_sdk = sdk.SnetSDK(config)
```

The `config` parameter is a Python dictionary.
See [test_sdk_client.py](https://github.com/singnet/snet-sdk-python/blob/master/testcases/functional_tests/test_sdk_client.py) for a reference.
#### Config options description

private_key: Your wallet's private key that will be used to pay for calls. Is **required** to make a call;   
eth_rpc_endpoint: RPC endpoint that is used to access the Ethereum network. Is **required** to make a call;   
email: Your email;  
identity_name: Name that will be used locally to save your wallet settings. You can check your identities in the `~/.snet/config` file;   
identity_type: Type of your wallet authentication. Note that snet-sdk currently supports only "key" identity_type;   
network: You can set the Ethereum network that will be used to make a call;   
force_update: If set to False, will reuse the existing gRPC stubs (if any) instead of downloading proto and regenerating them every time.   

##### List organizations and their services

You can use the sdk client instance`s methods get_organization_list() to list all organizations and get_services_list("org_id") to list all services of a given organization.  

```python
print(snet_sdk.get_organization_list())
print(snet_sdk.get_services_list("26072b8b6a0e448180f8c0e702ab6d2f"))
```

##### Free call configuration

If you want to use the free calls you will need to pass these arguments to the create_service_client() method:

```         
"free_call_auth_token-bin":"f2548d27ffd319b9c05918eeac15ebab934e5cfcd68e1ec3db2b92765",
"free-call-token-expiry-block":172800,
```
You can receive these for a given service from the [Dapp](https://beta.singularitynet.io/)
#### Calling the service
Now, the instance of the sdk can be used to create the service client instances.  
Continuing from the previous code here is an example using `Exampleservice` from the `26072b8b6a0e448180f8c0e702ab6d2f` organization:

```python
service_client = snet_sdk.create_service_client(org_id="26072b8b6a0e448180f8c0e702ab6d2f", 
                                                service_id="Exampleservice",
                                                group_name="default_group")
```
Creating a service client with free calls included would look like this:
```python
service_client = snet_sdk.create_service_client(org_id="26072b8b6a0e448180f8c0e702ab6d2f", 
                                                service_id="Exampleservice",
                                                group_name="default_group",
                                                free_call_auth_token_bin="f2548d27ffd319b9c05918eeac15ebab934e5cfcd68e1ec3db2b92765",
                                                free_call_token_expiry_block=172800)
```

After executing this code, you should have client libraries created for this service. They are located at the following path: `~/.snet/org_id/service_id/python/`

Note: Currently you can only save files to `~/.snet/`. We will fix this in the future.   
```python
service_client.deposit_and_open_channel(123456, 33333)
```
`deposit_and_open_channel(amount, expiration)` function deposits the specified amount of AGIX tokens in cogs into an MPE smart contract and opens a payment channel. Expiration is payment channel's TTL in blocks.    
The instance of service_client that has been generated can be utilized to invoke the methods that the service offers. You can list these using the get_services_and_messages_info_as_pretty_string() method:
```python
print(service_client.get_services_and_messages_info_as_pretty_string())
```

To invoke the service`s methods, you can use the the call_rpc() method. This method requires the names of the method and data object, along with the data itself, to be passed into it. 
To continue with our example, here’s a call to the *mul* method of the *Exampleservice* from the *26072b8b6a0e448180f8c0e702ab6d2f* organization:

```python
result = service_client.call_rpc("mul", "Numbers", a=20, b=3)
print(f"Calculating 20 * 3: {result}") #  Calculating 20 * 3: 60.0
```

For more information about gRPC and how to use it with Python, please see:
- [gRPC Basics - Python](https://grpc.io/docs/tutorials/basic/python.html)
- [gRPC Python’s documentation](https://grpc.io/grpc/python/)

---

## Development

### Installing

#### Prerequisites

* [Python 3.10](https://www.python.org/downloads/release/python-31012/)  

---

* Clone the git repository  
```bash  
$ git clone git@github.com:singnet/snet-sdk-python.git
$ cd snet-sdk-python
```

* Install the required dependencies
```bash
$ pip install -r requirements.txt
```

* Install the package in development/editable mode  
```bash  
$ pip install -e .
```

## License  
  
This project is licensed under the MIT License - see the
[LICENSE](https://github.com/singnet/snet-sdk-python/blob/master/LICENSE) file for details.