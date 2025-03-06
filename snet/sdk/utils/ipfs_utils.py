""" Utilities related to ipfs """
from typing import Any

import base58   # noqa F401
import ipfshttpclient
import multihash

from snet.sdk.config import Config


def get_from_ipfs_and_checkhash(ipfs_client: ipfshttpclient.Client,
                                ipfs_hash_base58: str,
                                validate: bool = True) -> Any:
    """
    Get file from IPFS. If validate is True,
    verify the integrity of the file using its hash.
    """

    data = ipfs_client.cat(ipfs_hash_base58)

    if validate:
        block_data = ipfs_client.block.get(ipfs_hash_base58)

        # print(f"IPFS hash (Base58): {ipfs_hash_base58}")
        # print(f"Block data length: {len(block_data)}")

        # Decode Base58 bash to multihash
        try:
            mh = multihash.decode(ipfs_hash_base58.encode('ascii'), "base58")
        except Exception as e:
            raise ValueError(f"Invalid multihash for IPFS hash: "
                             f"{ipfs_hash_base58}. Error: {str(e)}") from e

        # Correctly using mh instance for verification
        if not mh.verify(block_data):
            raise Exception("IPFS hash mismatch with data")

    return data


def get_ipfs_client(config: Config) -> ipfshttpclient.Client:
    ipfs_endpoint = config.get_ipfs_endpoint()
    return ipfshttpclient.connect(ipfs_endpoint)
