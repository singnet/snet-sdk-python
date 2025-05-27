import json
import sys
import importlib.resources
from urllib.parse import urlparse
from pathlib import Path, PurePath
import os
import tarfile
import io

import web3
from eth_typing import BlockNumber
from grpc_tools.protoc import main as protoc

from snet import sdk

RESOURCES_PATH = PurePath(os.path.dirname(sdk.__file__)).joinpath("resources")


def safe_address_converter(a):
    if not web3.Web3.is_checksum_address(a):
        raise Exception("%s is not is not a valid Ethereum checksum address" % a)
    return a


def type_converter(t):
    if t.endswith("[]"):
        return lambda x: list(map(type_converter(t.replace("[]", "")), json.loads(x)))
    else:
        if "int" in t:
            return lambda x: web3.Web3.to_int(text=x)
        elif "bytes32" in t:
            return lambda x: web3.Web3.to_bytes(text=x).ljust(32, b"\0") if not x.startswith(
                "0x") else web3.Web3.to_bytes(hexstr=x).ljust(32, b"\0")
        elif "byte" in t:
            return lambda x: web3.Web3.to_bytes(text=x) if not x.startswith("0x") else web3.Web3.to_bytes(hexstr=x)
        elif "address" in t:
            return safe_address_converter
        else:
            return str


def bytes32_to_str(b):
    return b.rstrip(b"\0").decode("utf-8")


def compile_proto(
    entry_path: Path,
    codegen_dir: Path,
    proto_file: str | None = None,
    target_language: str = "python",
    add_training: bool = False
) -> bool:
    try:
        if not os.path.exists(codegen_dir):
            os.makedirs(codegen_dir)
        proto_include = importlib.resources.files('grpc_tools') / '_proto'

        compiler_args = [
            "-I{}".format(entry_path),
            "-I{}".format(proto_include)
        ]

        if add_training:
            training_include = RESOURCES_PATH.joinpath("proto", "training")
            compiler_args.append("-I{}".format(training_include))

        if target_language == "python":
            compiler_args.insert(0, "protoc")
            compiler_args.append("--python_out={}".format(codegen_dir))
            compiler_args.append("--grpc_python_out={}".format(codegen_dir))
            compiler = protoc
        else:
            raise Exception("We only support python target language for proto compiling")

        if proto_file:
            compiler_args.append(str(proto_file))
        else:
            compiler_args.extend([str(p) for p in entry_path.glob("**/*.proto")])

        if add_training:
            compiler_args.append(str(training_include.joinpath("training.proto")))

        if not compiler(compiler_args):
            return True
        else:
            return False

    except Exception as e:
        print(e)
        return False


def is_valid_endpoint(url):
    """
    Just ensures the url has a scheme (http/https), and a net location (IP or domain name).
    Can make more advanced or do on-network tests if needed, but this is really just to catch obvious errors.
    >>> is_valid_endpoint("https://34.216.72.29:6206")
    True
    >>> is_valid_endpoint("blahblah")
    False
    >>> is_valid_endpoint("blah://34.216.72.29")
    False
    >>> is_valid_endpoint("http://34.216.72.29:%%%")
    False
    >>> is_valid_endpoint("http://192.168.0.2:9999")
    True
    """
    try:
        result = urlparse(url)
        if result.port:
            _port = int(result.port)
        return (
                all([result.scheme, result.netloc]) and
                result.scheme in ['http', 'https']
        )
    except ValueError:
        return False


def normalize_private_key(private_key):
    if private_key.startswith("0x"):
        private_key = bytes(bytearray.fromhex(private_key[2:]))
    else:
        private_key = bytes(bytearray.fromhex(private_key))
    return private_key


def get_address_from_private(private_key):
    return web3.Account.from_key(private_key).address


def get_current_block_number() -> BlockNumber:
    return web3.Web3().eth.block_number


class add_to_path:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            pass


def find_file_by_keyword(directory, keyword, exclude=None):
    if exclude is None:
        exclude = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if keyword in file and all(e not in file for e in exclude):
                return file


def bytesuri_to_hash(s, to_decode=True):
    if to_decode:
        s = s.rstrip(b"\0").decode('ascii')
    if s.startswith("ipfs://"):
        return "ipfs", s[7:]
    elif s.startswith("filecoin://"):
        return "filecoin", s[11:]
    else:
        raise Exception("We support only ipfs and filecoin uri in Registry")


def safe_extract_proto(spec_tar, protodir):
    """
    Tar files might be dangerous (see https://bugs.python.org/issue21109,
    and https://docs.python.org/3/library/tarfile.html, TarFile.extractall warning)
    we extract only simple files
    """
    with tarfile.open(fileobj=io.BytesIO(spec_tar)) as f:
        for m in f.getmembers():
            if os.path.dirname(m.name) != "":
                raise Exception(
                    "tarball has directories. We do not support it.")
            if not m.isfile():
                raise Exception(
                    "tarball contains %s which is not a file" % m.name)
            fullname = os.path.join(protodir, m.name)
            if os.path.exists(fullname):
                os.remove(fullname)
                print(f"{fullname} removed.")
        # now it is safe to call extractall
        f.extractall(path=protodir)
