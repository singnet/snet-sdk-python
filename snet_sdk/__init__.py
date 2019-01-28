import sys
import os 
import importlib
import json
from pathlib import PurePath, Path

import grpc

__version__ = "0.0.1"

dir_path = PurePath(os.path.abspath(sys.modules['__main__'].__file__)).parent

class Snet:
    def __init__(
        self,
        libraries_base_path="grpc",
    ):
        self.libraries_base_path = libraries_base_path

    def client(self, _org_id, _service_id, service_endpoint):
        client = {}

        # Import modules and add them to client grpc object
        libraries_base_path = self.libraries_base_path
        org_id = _org_id
        service_id = _service_id 

        client_library_path = str(dir_path.joinpath(self.libraries_base_path, org_id, service_id))
        sys.path.insert(0, client_library_path)

        grpc_modules = []
        for module_path in Path(client_library_path).glob("**/*_pb2.py"):
            grpc_modules.append(module_path)
        for module_path in Path(client_library_path).glob("**/*_pb2_grpc.py"):
            grpc_modules.append(module_path)

        grpc_modules = list(map(
            lambda x: str(PurePath(Path(x).relative_to(client_library_path).parent.joinpath(PurePath(x).stem))),
            grpc_modules
        ))

        imported_modules = {}
        for grpc_module in grpc_modules:
            imported_module = importlib.import_module(grpc_module)
            imported_modules[grpc_module] = imported_module

        sys.path.remove(client_library_path)
        client["grpc"] = imported_modules

        # Instantiate grpc channel for service
        client["channel"] = grpc.insecure_channel(service_endpoint)

        return client 
