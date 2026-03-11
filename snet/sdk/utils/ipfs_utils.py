import ipfshttpclient
import multihash
import hashlib


def get_from_ipfs_and_checkhash(ipfs_client, ipfs_hash_base58, validate=True):
    """
    Get file from IPFS and validate hash
    """
    data = ipfs_client.cat(ipfs_hash_base58)

    if validate:
        block_data = ipfs_client.block.get(ipfs_hash_base58)

        try:
            mh_bytes = multihash.from_b58_string(ipfs_hash_base58)
            decoded = multihash.decode(mh_bytes)

            hash_func_name = decoded.name
            expected_digest = decoded.digest

            if hash_func_name == "sha2-256":  # Standard for IPFS (CIDv0)
                actual_digest = hashlib.sha256(block_data).digest()
            else:
                # Handle other algorithms supported by hashlib if necessary
                h = hashlib.new(hash_func_name.replace("-", ""))
                h.update(block_data)
                actual_digest = h.digest()

            if actual_digest != expected_digest:
                raise Exception("IPFS hash mismatch with data")

        except Exception as e:
            raise ValueError(f"Integrity check failed: {str(e)}") from e

    return data


def get_ipfs_client(config):
    ipfs_endpoint = config.get_ipfs_endpoint()
    return ipfshttpclient.connect(ipfs_endpoint)
