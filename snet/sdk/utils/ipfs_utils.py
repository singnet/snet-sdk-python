""" Utilities related to ipfs """
import base58
import ipfshttpclient
import multihash


def get_from_ipfs_and_checkhash(ipfs_client, ipfs_hash_base58, validate=True):
    """
    Get file from ipfs
    We must check the hash becasue we cannot believe that ipfs_client wasn't been compromise
    """
    if validate:
        from snet.sdk.resources.proto.unixfs_pb2 import Data
        from snet.sdk.resources.proto.merckledag_pb2 import MerkleNode

        # No nice Python library to parse ipfs blocks, so do it ourselves.
        block_data = ipfs_client.block.get(ipfs_hash_base58)
        mn = MerkleNode()
        mn.ParseFromString(block_data)
        unixfs_data = Data()
        unixfs_data.ParseFromString(mn.Data)
        assert unixfs_data.Type == unixfs_data.DataType.Value(
            'File'), "IPFS hash must be a file"
        data = unixfs_data.Data

        # multihash has a badly registered base58 codec, overwrite it...
        multihash.CodecReg.register(
            'base58', base58.b58encode, base58.b58decode)
        # create a multihash object from our ipfs hash
        mh = multihash.decode(ipfs_hash_base58.encode('ascii'), 'base58')

        # Convenience method lets us directly use a multihash to verify data
        if not mh.verify(block_data):
            raise Exception("IPFS hash mismatch with data")
    else:
        data = ipfs_client.cat(ipfs_hash_base58)
    return data

def get_ipfs_client(config):
    ipfs_endpoint = config.get_ipfs_endpoint()
    return ipfshttpclient.connect(ipfs_endpoint)

