## module: sdk.utils.utils

[Link](https://github.com/singnet/snet-sdk-python/blob/master/snet/sdk/utils/utils.py) to GitHub

Entities:
1. [safe_address_converter](#function-safe_address_converter)
2. [type_converter](#function-type_converter)
3. [bytes32_to_str](#function-bytes32_to_str)
4. [compile_proto](#function-compile_proto)
5. [is_valid_endpoint](#function-is_valid_endpoint)
6. [normalize_private_key](#function-normalize_private_key)
7. [get_address_from_private](#function-get_address_from_private)
8. [add_to_path](#class-add_to_path)
9. [find_file_by_keyword](#function-find_file_by_keyword)


### Function `safe_address_converter`

Checks if the address is a valid checksum address and returns it, otherwise raises an exception.

###### args:

- `a` (Any): The address to check.

###### returns:

- The address if it is valid. (Any)

###### raises:

- `Exception`: If the address isn't a valid checksum address.

### Function `type_converter

Creates a function that converts a value to the specified type.

###### args:

- `t` (Any): The type to convert the value to.

###### returns:

- A function that converts the value to the specified type. (Any -> Any)

### Function `bytes32_to_str`

Converts a bytes32 value to a string.

###### args:

- `b` (bytes): The bytes32 value to convert.

###### returns:

- The string representation of the bytes32 value. (str)

### Function `compile_proto`

Compiles Protocol Buffer (protobuf) files into code for a specific target language.
Generated files as well as .proto files are stored in the `~/.snet` directory.

###### args:

- `entry_path` (Path): The path to the .proto file.
- `codegen_dir` (PurePath): The directory where the compiled code will be generated.
- `proto_file` (str): The name of the .proto file to compile. Defaults to `None`.
- `target_language` (str, optional): The target language for the compiled code. Defaults to "python".

###### returns:

- True if the compilation is successful, False otherwise. (bool)

###### raises:

- `Exception`: If the error occurs while performing the function.

### Function `is_valid_endpoint`

Checks if the given endpoint is valid.

###### args:

- `url` (str): The endpoint to check.

###### returns:

- True if the endpoint is valid, False otherwise. (bool)

###### raises:

- `ValueError`: If the error occurs while performing the function.

### Function `normalize_private_key`

Returns the normalized private key.

###### args:

- `private_key` (str): The private key in hex format to normalize.

###### returns:

- The normalized private key. (bytes)

### Function `get_address_from_private`

Returns the wallet address from the private key.

###### args:

- `private_key` (Any): The private key.

###### returns:

- The wallet address. (ChecksumAddress)

### Class `add_to_path`

`add_to_path` class is a _**context manager**_ that temporarily adds a given path to the system's `sys.path` list. 
This allows for the import of modules or packages from that path. The `__enter__` method is called when the context 
manager is entered, and it inserts the path at the beginning of sys.path. The `__exit__` method is called when the 
context manager is exited, and it removes the path from sys.path.

###### args:

- `path` (str): The path to add to sys.path.

### Function `find_file_by_keyword`

Finds a file by keyword in the current directory and subdirectories.

###### args:

- `directory` (AnyStr | PathLike[AnyStr]): The directory to search in.
- `keyword` (AnyStr): The keyword to search for.

###### returns:

- The name of the file that contains the keyword, or `None` if no file is found. (AnyStr | None)

