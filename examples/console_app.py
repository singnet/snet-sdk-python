from snet.sdk import SnetSDK
from snet.sdk.service_client import ServiceClient


def initialize_by_default():
    org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
    service_id = "Exampleservice"
    group_name = "default_group"
    service = snet_sdk.create_service_client(org_id=org_id, service_id=service_id, group_name=group_name)
    services[(service.org_id, service.service_id)] = service
    global active_service
    active_service = service


def get_group_name(service_client):
    service_client


def list_organizations():
    print("Organizations:")
    print(*map(lambda x: '\t' + x, snet_sdk.get_organization_list()), sep="\n")


def list_services_for_org():
    org_id = input("Enter organization id: ")
    print("Services:")
    print(*map(lambda x: '\t' + x, snet_sdk.get_services_list(org_id=org_id)), sep="\n")


def create_service_client():
    org_id = input("Enter organization id: ")
    service_id = input("Enter service id: ")
    group_name = input("Enter payment group name: ")
    service = snet_sdk.create_service_client(org_id=org_id, service_id=service_id, group_name=group_name)
    services[(service.org_id, service.service_id)] = service


def commands_help():
    print("Available commands:")
    print(*map(lambda x: '\t' + x, commands.keys()), sep="\n")


def change_config():
    pass


def list_initialized_services():
    print("Initialized services:")
    print("Organization_id    Service_id    Group_name")
    print(*map(lambda service: f"{service.org_id}  {service.service_id}  {service.group['group_name']}", services.values()), sep="\n")


def switch_service():
    list_initialized_services()
    org_id, service_id = input("Enter organization id and service id (by space): ").split()
    if (org_id, service_id) in services.keys():
        global active_service
        active_service = services[(org_id, service_id)]
    else:
        print(f"Service with {org_id} organization id and {service_id} service id is not initialized")


def call():
    if active_service is None:
        print("No active service. Please enter 'switch-service' to switch service")
        return None

    method_name = input("Enter method name: ")

    servs, msgs = active_service.get_services_and_messages_info()
    is_found = False
    for service in servs.items():
        for method in service[1]:
            print(method[0], method_name)
            if method[0] == method_name:
                input_type = method[1]
                output_type = method[2]
                is_found = True
                break
        if is_found:
            break

    if not is_found:
        print(f"Method '{method_name}' is not found in service")
        return None

    inputs = {var[1]: float(input(f"{var[1]}: ")) for var in msgs[input_type]}

    print("Service calling...")

    result = active_service.call_rpc(method_name, input_type, **inputs)
    outputs = {var[1]: getattr(result, var[1]) for var in msgs[output_type]}

    print("Result:", *map(lambda x: f"{x[0]}: {x[1]}", outputs.items()), sep="\n")


def print_service_info():
    if active_service is None:
        print("No active service")
        return None

    print(active_service.get_services_and_messages_info_as_pretty_string())


config = {
    "private_key": 'APP_PROVIDER_PRIVATE_KEY',
    "eth_rpc_endpoint": f"https://sepolia.infura.io/v3/INFURE_API_KEY",
    "concurrency": False,
    "identity_name": "NAME",
    "identity_type": "key",
    "network": "sepolia",
    "force_update": False
}

snet_sdk = SnetSDK(config)
services = {}
active_service: ServiceClient = None
initialize_by_default()

commands = {
    "list-orgs": list_organizations,
    "list-services-for-org": list_services_for_org,
    "add-service": create_service_client,
    "help": commands_help,
    "exit": lambda: exit(0),
    "change-config": change_config,
    "list-initialized-services": list_initialized_services,
    "switch-service": switch_service,
    "call": call,
    "print-service-info": print_service_info,

}


def main():
    print("""
Hello, welcome to the Snet SDK console application!
To use the application, type the name of the command you want to execute.
To print the list of available commands, type 'help'.""")
    while True:
        command = input(">>> ")
        if command in commands:
            commands[command]()
        else:
            print(f"Command '{command}' is not found. Please try again.")


if __name__ == "__main__":
    main()
