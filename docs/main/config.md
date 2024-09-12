## module: sdk.config

[Link](https://github.com/singnet/snet-sdk-python/blob/master/snet/sdk/config.py) to GitHub

Entities:
1. [Config](#class-clientlibgenerator)
   - [\_\_init\_\_](#__init__)
   - [get_session_network_name](#get_session_network_name)
   - [safe_get_session_identity_network_names](#safe_get_session_identity_network_names)
   - [set_session_network](#set_session_network)
   - [_set_session_network](#_set_session_network)
   - [set_session_identity](#set_session_identity)
   - [get_session_field](#get_session_field)
   - [set_session_field](#set_session_field)
   - [unset_session_field](#unset_session_field)
   - [session_to_dict](#session_to_dict)
   - [add_network](#add_network)
   - [set_network_field](#set_network_field)
   - [add_identity](#add_identity)
   - [set_identity_field](#set_identity_field)
   - [_get_network_section](#_get_network_section)
   - [_get_identity_section](#_get_identity_section)
   - [get_ipfs_endpoint](#get_ipfs_endpoint)
   - [set_ipfs_endpoint](#set_ipfs_endpoint)
   - [get_all_identities_names](#get_all_identities_names)
   - [get_all_networks_names](#get_all_networks_names)
   - [delete_identity](#delete_identity)
   - [create_default_config](#create_default_config)
   - [_check_section](#_check_section)
   - [_persist](#_persist)
   - [get_param_from_sdk_config](#get_param_from_sdk_config)
   - [setup_identity](#setup_identity)
2. [first_identity_message_and_exit](#function-first_identity_message_and_exit)
3. [get_session_identity_keys](#function-get_session_identity_keys)
4. [get_session_network_keys](#function-get_session_network_keys)
5. [get_session_network_keys_removable](#function-get_session_network_keys_removable)
6. [get_session_keys](#function-get_session_keys)

### Class `Config`

extends: `ConfigParser`

is extended by: -

#### description

This is a configuration manager for the SDK. It is responsible for handling configuration settings for the SDK.

#### attributes

- `_config_file` (Path): The path to the configuration file.
- `sdk_config` (dict): The SDK configuration.
- `is_sdk` (bool): Whether the configuration is for the SDK.

#### methods

#### `__init__`

Initializes a new instance of the class. Reads the configuration file or creates a default one if it doesn't exist.
Initializes attributes by the passed arguments.

###### args:

- `_snet_folder` (Path): The path to the folder where the configuration file is located. Defaults to "~/.snet".
- `sdk_config` (dict): The SDK configuration. Defaults to _None_.

###### returns:

- _None_

#### `get_session_network_name`

Returns the name of the session network.

###### returns:

- (str): The name of the session network.

#### `safe_get_session_identity_network_names`

Returns the names of the session network and identity.

###### returns:

- The names of the session network and identity. (str, str)

###### raises:

- Exception: If the session identity does not bind to the session network.

#### `set_session_network`

Sets the session network using `_set_session_network`.

###### args:

- `network` (str): The name of the session network.
- `out_f` (TextIO): The output to write messages to.

###### returns:

- _None_

#### `_set_session_network`

Sets the session network.

###### args:

- `network` (str): The name of the session network.
- `out_f` (TextIO): The output to write messages to.

###### returns:

- _None_

###### raises:

- Exception: If the network is not in the config.

#### `set_session_identity`

Sets the session identity.

###### args:

- `identity` (str): The name of the session identity.
- `out_f` (TextIO): The output to write messages to.

###### returns:

- _None_

###### raises:

- Exception: If the identity is not in the config.

#### `get_session_field`

Retrieves a session field based on the provided key.

###### args:

- `key` (str): The key of the session field to retrieve.
- `exception_if_not_found` (bool): Whether to raise an exception if the field is not found. Defaults to _True_.

###### returns:

- The value of the session field if found, otherwise _None_. (str | None)

###### raises:

- `Exception`: If the field is not found and `exception_if_not_found` is _True_.

#### `set_session_field`

Sets a session field based on the provided key and value.

###### args:

- `key` (str): The key of the session field to set.
- `value` (str): The value of the session field to set.
- `out_f` (TextIO): The output to write messages to.

###### returns:

- _None_

###### raises:

- `Exception`: If the key is not in the config.

#### `unset_session_field`

Unsets a session field based on the provided key.

###### args:

- `key` (str): The key of the session field to unset.
- `out_f` (TextIO): The output to write messages to.

###### returns:

- _None_

#### `session_to_dict`

Converts the session configuration to a dictionary.

###### returns:

- The session configuration as a dictionary. (dict)

#### `add_network`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `set_network_field`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `add_identity`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `set_identity_field`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `_get_network_section`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `_get_identity_section`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `get_ipfs_endpoint`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `get_all_identities_names`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `get_all_networks_names`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `delete_identity`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `create_default_config`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `_check_section`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `_persist`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `get_param_from_sdk_config`



###### args:

- 

###### returns:

- 

###### raises:

- 

#### `setup_identity`



###### args:

- 

###### returns:

- 

###### raises:

- 

### Function `first_identity_message_and_exit`



###### args:

- 

###### returns:

- 

###### raises:

- 

### Function `get_session_identity_keys`



###### args:

- 

###### returns:

- 

###### raises:

- 

### Function `get_session_network_keys`



###### args:

- 

###### returns:

- 

###### raises:

- 

### Function `get_session_network_keys_removable`



###### args:

- 

###### returns:

- 

###### raises:

- 

### Function `get_session_keys`



###### args:

- 

###### returns:

- 

###### raises:

- 

