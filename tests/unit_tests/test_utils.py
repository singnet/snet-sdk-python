import sys
import unittest
from unittest.mock import patch, MagicMock

from snet.sdk.utils.utils import (
    add_to_path, bytes32_to_str, bytesuri_to_hash, compile_proto,
    find_file_by_keyword, get_address_from_private, is_valid_endpoint,
    normalize_private_key, safe_address_converter, safe_extract_proto,
    type_converter
)


class TestUtils(unittest.TestCase):

    def test_safe_address_converter_valid(self):
        valid_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.assertEqual(safe_address_converter(valid_address), valid_address)

    def test_safe_address_converter_invalid(self):
        invalid_address = "0x1234"
        with self.assertRaises(Exception):
            safe_address_converter(invalid_address)

    def test_type_converter(self):
        list_converter = type_converter("int[]")
        self.assertEqual(list_converter("[1, 2, 3]"), [1, 2, 3])

        converter = type_converter("int")
        self.assertEqual(converter("123"), 123)

        converter = type_converter("bytes32")
        input_str = "test"
        expected_result = bytes(input_str, encoding="utf-8").ljust(32, b"\0")
        self.assertEqual(converter(input_str), expected_result)
        hex_input = "0x1234"
        expected_result = bytes.fromhex(hex_input[2:]).ljust(32, b"\0")
        self.assertEqual(converter(hex_input), expected_result)

        converter = type_converter("byte")
        self.assertEqual(converter("123"), bytes("123", encoding="utf-8"))

        converter = type_converter("address")
        address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        self.assertEqual(converter(address), address)

        converter = type_converter("str")
        self.assertEqual(converter("123"), "123")

    def test_bytes32_to_str(self):
        self.assertEqual(bytes32_to_str(b"test\x00\x00"), "test")

    # @patch("snet.sdk.utils.utils.protoc")
    # def test_compile_proto_python(self, mock_protoc):
    #     mock_protoc.return_value = True
    #     entry_path = codegen_dir = Path("/some/path")
    #     result = compile_proto(entry_path, codegen_dir, target_language="python")
    #     self.assertTrue(result)

    def test_is_valid_endpoint(self):
        self.assertTrue(is_valid_endpoint("https://example.com"))
        self.assertTrue(is_valid_endpoint(b"https://example.com"))
        self.assertTrue(is_valid_endpoint("https://example.com/path?id=17"))
        self.assertTrue(is_valid_endpoint(b"https://example.com/path?id=17"))
        self.assertFalse(is_valid_endpoint("ftp://example.com"))
        self.assertFalse(is_valid_endpoint(b"ftp://example.com"))
        self.assertFalse(is_valid_endpoint("http://example:99999"))
        self.assertFalse(is_valid_endpoint(b"http://example:99999"))

    def test_normalize_private_key(self):
        private_key = "0x0123456789abcdef"
        normalized = normalize_private_key(private_key)
        self.assertEqual(normalized, b"\x01#Eg\x89\xab\xcd\xef")

        private_key = "0123456789abcdef"
        normalized = normalize_private_key(private_key)
        self.assertEqual(normalized, b"\x01#Eg\x89\xab\xcd\xef")

    @patch("web3.Account.from_key")
    def test_get_address_from_private(self, mock_from_key):
        mock_from_key.return_value = MagicMock(address="0x123")
        self.assertEqual(get_address_from_private("0x456"), "0x123")

    def test_add_to_path(self):
        path = "/some/path"
        with add_to_path(path):
            self.assertIn(path, sys.path)
        self.assertNotIn(path, sys.path)

    @patch("os.walk")
    def test_find_file_by_keyword(self, mock_walk):
        mock_walk.return_value = [("/root", [], ["file.txt", "key_file.txt"])]
        result = find_file_by_keyword("/root", "key")
        self.assertEqual(result, "key_file.txt")

    def test_bytesuri_to_hash_without_decode(self):
        # IPFS
        uri = "ipfs://example"
        result = bytesuri_to_hash(uri, to_decode=False)
        self.assertEqual(result, ("ipfs", "example"))

        # Filecoin
        uri = "filecoin://example"
        result = bytesuri_to_hash(uri, to_decode=False)
        self.assertEqual(result, ("filecoin", "example"))

        # Invalid
        uri = "unsupported://example"
        with self.assertRaises(Exception) as context:
            bytesuri_to_hash(uri, to_decode=False)

        self.assertEqual(str(context.exception),
                         "We support only ipfs and filecoin uri in Registry")

    def test_bytesuri_to_hash_with_decode(self):
        # IPFS
        uri = b"ipfs://example\x00"
        self.assertEqual(bytesuri_to_hash(uri), ("ipfs", "example"))

        # Filecoin
        uri = b"filecoin://example\x00"
        self.assertEqual(bytesuri_to_hash(uri), ("filecoin", "example"))

        # Invalid
        uri = b"unsupported://example\x00"
        with self.assertRaises(Exception) as context:
            bytesuri_to_hash(uri)

        self.assertEqual(str(context.exception),
                         "We support only ipfs and filecoin uri in Registry")

    # @patch("os.makedirs")
    # def test_safe_extract_proto(self, mock_makedirs):
    #     spec_tar = io.BytesIO()
    #     with tarfile.open(fileobj=spec_tar, mode="w") as tar:
    #         file_data = io.BytesIO(b"content")
    #         tarinfo = tarfile.TarInfo(name="test.proto")
    #         tarinfo.size = len(file_data.getvalue())
    #         tar.addfile(tarinfo, file_data)

    #     #protodir = "/tmp/protodir"
    #     #mock_makedirs(protodir, exist_ok=True)

    #     #mock_makedirs.assert_called_once_with(exist_ok=True)
    #     with patch("tarfile.open") as mock_open:
    #         mock_open.return_value = tarfile.open(fileobj=spec_tar)
    #         safe_extract_proto(spec_tar.getvalue(), protodir)
    #         self.assertTrue(os.path.exists(os.path.join(protodir, "test.proto")))


if __name__ == "__main__":
    unittest.main()
