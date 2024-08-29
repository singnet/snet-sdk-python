from snet.sdk import SnetSDK
from snet.sdk.service_client import ServiceClient


def initialize_by_default():
    org_id = "26072b8b6a0e448180f8c0e702ab6d2f"
    service_id = "Exampleservice"
    group_name = "default_group"
    service = snet_sdk.create_service_client(org_id=org_id, service_id=service_id, group_name=group_name)
    initialized_services.append(service)
    global active_service
    active_service = service


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

    have_free_calls = input("Use free calls? (y/n): ") == 'y'
    free_call_token = None
    free_call_token_expiry_block = None
    if have_free_calls:
        free_call_token = input("Enter free call auth token: ")
        free_call_token_expiry_block = input("Enter free call token expiry block: ")

    service = snet_sdk.create_service_client(org_id=org_id, service_id=service_id, group_name=group_name,
                                             free_call_auth_token_bin=free_call_token,
                                             free_call_token_expiry_block=free_call_token_expiry_block)
    initialized_services.append(service)

    global active_service
    if active_service is None:
        active_service = service


def commands_help():
    global active_commands
    print("Available commands:")
    for command in active_commands.items():
        print(f'\t{command[0]} - {command[1][1]}')


def change_config():
    pass


def list_initialized_services():
    print("INDEX    ORGANIZATION_ID    SERVICE_ID    GROUP_NAME")
    for index, service in enumerate(initialized_services):
        print(f"{index}  {service.org_id}  {service.service_id}  {service.group['group_name']}")


def switch_service():
    list_initialized_services()
    index = int(input("Enter the index of one of the initialized services: "))
    if index < len(initialized_services):
        global active_service
        active_service = initialized_services[index]
        print(f"Switched to service with index {index}")
    else:
        print(f"Service with index {index} is not initialized!")


def call():
    global active_service
    if active_service is None:
        print("No initialized services!\n"
              "Please enter 'service' to go to the service menu and then enter 'add' to add a service.")
        return None

    method_name = input("Enter method name: ")

    services, msgs = active_service.get_services_and_messages_info()
    is_found = False
    for service in services.items():
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
    global active_service
    if active_service is None:
        print("No initialized services!\n"
              "Please enter 'service' to go to the service menu and then enter 'add' to add a service.")
        return None
    print(active_service.get_services_and_messages_info_as_pretty_string())


def deposit():
    amount = int(input("Enter amount of AGIX tokens in cogs to deposit into an MPE account: "))
    snet_sdk.account.deposit_to_escrow_account(amount)


def open_channel():
    global active_service
    additions = False
    if active_service is None:
        additions = input("No initialized services! This entails entering additional parameters. Continue? (y/n): ") == 'y'
        if not additions:
            return None
    else:
        is_continue = input("The new channel will be opened for the active service. Continue? (y/n): ") == 'y'
        if not is_continue:
            return None

    amount = int(input("Enter amount of AGIX tokens in cogs to put into the channel: "))

    balance = snet_sdk.account.escrow_balance()
    is_deposit = False
    if balance < amount:
        print(f"Insufficient balance!\n\tCurrent MPE balance: {balance}\n\tAmount to put: {amount}")
        is_deposit = input("Would you like to deposit needed amount of AGIX tokens in advance? (y/n): ") == 'y'
        if not is_deposit:
            print("Channel is not opened!")
            return None

    expiration = int(input("Enter expiration time in blocks: "))

    if additions:
        payment_address = input("Enter payment address: ")
        group_id = input("Enter payment group id: ")
        if is_deposit:
            snet_sdk.mpe_contract.deposit_and_open_channel(account=snet_sdk.account,
                                                           payment_address=payment_address,
                                                           group_id=group_id,
                                                           amount=amount,
                                                           expiration=expiration)
        else:
            snet_sdk.mpe_contract.open_channel(account=snet_sdk.account,
                                               payment_address=payment_address,
                                               group_id=group_id,
                                               amount=amount,
                                               expiration=expiration)
    else:
        if is_deposit:
            active_service.open_channel(amount=amount, expiration=expiration)
        else:
            active_service.deposit_and_open_channel(amount=amount, expiration=expiration)


def list_channels():
    pass


def add_funds():
    pass


def extend_expiration():
    pass


config = {
    "private_key": 'APP_PROVIDER_PRIVATE_KEY',
    "eth_rpc_endpoint": f"https://sepolia.infura.io/v3/APP_PROVIDER_INFURA_KEY",
    "concurrency": False,
    "identity_name": "NAME",
    "identity_type": "key",
    "network": "sepolia",
    "force_update": False
}

snet_sdk = SnetSDK(config)
initialized_services = []
active_service: ServiceClient
channels = {}
initialize_by_default()

commands = {
    "main": {
        "organizations": (list_organizations, "print a list of organization ids from Registry"),
        "services": (list_services_for_org, "print a list of service ids for an organization from Registry"),
        # "change-config": change_config,
        "deposit": (deposit, "deposit AGIX tokens into MPE"),
        "service": (lambda: None, "go to the services menu"),
        "channel": (lambda: None, "go to the channels menu"),
        "help": (commands_help, "print a list of available commands in the main menu"),
        "exit": (lambda: exit(0), "exit the application")
    },

    "service": {
        "add": (create_service_client,
                "create a new service client. If it the first time, the new service becomes active"),
        "use": (switch_service, "switch the active service"),
        "call": (call, "call the active service method"),
        "info": (print_service_info, "output services, methods and messages in a service"),
        "list": (list_initialized_services, "print a list of initialized services"),
        "help": (commands_help, "print a list of available commands in the services menu"),
        "back": (lambda: None, "return to the main menu"),
        "exit": (lambda: exit(0), "exit the application")
    },

    "channel": {
        "list": (list_channels, "print a list of initialized payment channels"),
        "open": (open_channel, "open a new payment channel"),
        "add-funds": (add_funds, "add funds to a channel"),
        "extend-expiration": (extend_expiration, "extend expiration of a channel"),
        "help": (commands_help, "print a list of available commands in the channels menu"),
        "back": (lambda: None, "return to the main menu"),
        "exit": (lambda: exit(0), "exit the application")
    }
}

active_commands: dict = commands["main"]


def main():
    global active_commands

    print("""
Hello, welcome to the Snet SDK console application!
To use the application, type the name of the command you want to execute.""")
    commands_help()
    print("To print a list of available commands, type 'help'")

    prefix = ">>> "
    while True:
        command = input(prefix)
        if command in active_commands:
            active_commands[command][0]()
        else:
            print(f"Command '{command}' is not found. Please try again.")
            continue

        if command in ["back", "service", "channel"]:
            if command == "back":
                command = "main"
                prefix = ">>> "
            else:
                prefix = command + " >>> "
            active_commands = commands[command]
            commands_help()


if __name__ == "__main__":
    main()
