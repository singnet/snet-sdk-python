# snet-sdk-python
  
SingularityNET SDK for Python

## Package

The package is published in PyPI at the following link:

|Package                                       |Description                                                          |
|----------------------------------------------|---------------------------------------------------------------------|
|[snet-sdk](https://pypi.org/project/snet.sdk/)|Integrate SingularityNET services seamlessly into Python applications|

## Getting Started  
  
These instructions are for the development and use of the SingularityNET SDK for Python.

### Core concepts

The SingularityNET SDK allows you to make calls to SingularityNET services programmatically from your application.
To communicate between clients and services, SingularityNET uses [gRPC](https://grpc.io/).
To handle payment of services, SingularityNET uses [Ethereum state channels](https://dev.singularitynet.io/docs/concepts/multi-party-escrow/).
The SingularityNET SDK abstracts and manages state channels with service providers on behalf of the user and handles authentication with the SingularityNET services.

### Usage

To call a SingularityNET service, the user must be able to deposit funds (AGI tokens) to the [Multi-Party Escrow](https://dev.singularitynet.io/docs/concepts/multi-party-escrow/) Smart Contract.
To deposit these tokens or do any other transaction on the Ethereum blockchain, the user must possess an Ethereum identity with available Ether.

Once you have installed the snet-sdk in your current environment and it's in your PYTHONPATH, you should import it and create an instance of the base sdk class:

```python
from snet import sdk
from config import config
snet_sdk = sdk.SnetSDK(config)
```

The `config` parameter must be a Python dictionary.  
See [test_sdk_client.py.sample](https://github.com/singnet/snet-cli/blob/master/packages/sdk/testcases/functional_tests/test_sdk_client.py) for a sample configuration file.

After executing this code, you should have client libraries created for this service. They are located in the following path: ~/.snet/org_id/service_id/python/

Note: Currently you can only save files to ~/.snet/

##### Free call configuration

If you want to use free call you need to add below mwntioned attributes in config file.
```         
"free_call_auth_token-bin":"f2548d27ffd319b9c05918eeac15ebab934e5cfcd68e1ec3db2b92765",
"free-call-token-expiry-block":172800,
"email":"test@test.com"  
```
You can download this config for a given service from [Dapp]([https://beta.singularitynet.io/)

Now, the instance of the sdk can be used to create service client instances.
Continuing from the previous code this is an example using `Exampleservicee` from the `26072b8b6a0e448180f8c0e702ab6d2f` organization:

```python
import example_service_pb2_grpc

org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
service_id = "Exampleservice"
group_name="default_group"

service_client = snet_sdk.create_service_client(org_id, service_id, group_name)
```

Note that `org_id` and `service_id` must be passed to `config`.

The generated service_client instance can be used to call methods provided by the service.
To call these methods, you need to use the call_rpc method, passing into it the names of the method and data object, as well as the data itself (What specific data needs to be passed can be seen in the .proto file).
Continuing from the previous code, this is an example using example-service from the snet organization:

```python
result = service_client.call_rpc("mul", "Numbers", a=20, b=3)
print(f"Performing 20 * 3: {result}") # Performing 20 * 3: value: 60.0
```

You can get this code example at [https://github.com/singnet/snet-code-examples/tree/python_client/python/client](https://github.com/singnet/snet-code-examples/tree/python_client/python/client)

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
