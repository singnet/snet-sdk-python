## module: sdk.\_\_init\_\_.py

Entities:
1. [Arguments](#class-arguments)
   - [\_\_init\_\_](#init)
2. [SnetSDK](#class-snetsdk)
   - [\_\_init\_\_](#init-1)

### class `Arguments`

extends: -

is extended by: -

#### description

Represents the arguments for the `BlockchainCommand` from `snet.cli`.

#### attributes

- `org_id` (str): The organization id.
- `service_id` (str): The service id.
- `language` (str): The language used. Defaults to "python".
- `protodir` (Path): The path to the directory with protobuf files. Defaults to "~/USER_NAME/.snet".

#### methods

##### `__init__`

Initializes a new instance of the class.

###### args:

- `org_id` (str): The organization id. Defaults to _None_.
- `service_id` (str): The service id. Defaults to _None_.

###### returns:

- _None_

### class `SnetSDK`

extends: -

is extended by: -

#### description

The SnetSDK class is the main entry point for interacting with the SingularityNET platform.
It provides methods for creating service clients, managing identities, and configuring the SDK.

#### attributes

- `_sdk_config` (dict): The SDK configuration.
- `_metadata_provider` (MetadataProvider): An instance of the `MetadataProvider` class. Note: There is currently only 
one implementation of `MetadataProvider` which is `IPFSMetadataProvider`, so this attribute can only be initialized to 
`IPFSMetadataProvider` at this time.
- `web3` (Web3): An instance of the Web3 class for interacting with the Ethereum blockchain.
- `mpe_contract` (MPEContract): An instance of the `MPEContract` class for interacting with the MultiPartyEscrow contract.
- `ipfs_client` (ipfshttpclient.Client): An instance of the `ipfshttpclient.Client` class for interacting with the 
InterPlanetary File System.
- `registry_contract` (Contract): An instance of the `Contract` class for interacting with the Registry contract.
- `account` (Account): An instance of the `Account` class for managing the SDK's Ethereum account.

#### methods

##### `__init__`

Initializes a new instance of the `SnetSDK` class. Initializes `web3` with the specified Ethereum RPC endpoint.
Instantiates the MPE contract with the specified contract address if provided, otherwise uses the default MPE contract.
Instantiates the IPFS client with the specified IPFS endpoint if provided, otherwise uses the default IPFS endpoint.
Instantiates the Registry contract with the specified contract address if provided, otherwise uses the default Registry 
contract. Instantiates the Account object with the specified Web3 client, SDK configuration, and MPE contract.
Creates an instance of the "Config" class, passing `_sdk_config` to it, and calls the `setup_config` method with this 
instance as an argument.

###### args:

- `sdk_config` (dict): A dictionary containing the SDK configuration.
- `metadata_provider` (MetadataProvider): A `MetadataProvider` object. Defaults to _None_.

###### returns:

- _None_

##### `setup_config`



###### args:

- 

###### returns:

- _None_

###### raises:

- Exception
