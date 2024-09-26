from snet import sdk

config = sdk.config.Config(private_key="YOUR_PRIVATE_KEY",
                               eth_rpc_endpoint=f"https://sepolia.infura.io/v3/YOUR_INFURA_KEY",
                               concurrency=False,
                               force_update=False)

operators = {
    "+": "add",
    "-": "sub",
    "*": "mul",
    "/": "div"
}

snet_sdk = sdk.SnetSDK(config)
calc_client = snet_sdk.create_service_client(org_id="26072b8b6a0e448180f8c0e702ab6d2f",
                                             service_id="Exampleservice", group_name="default_group")


def parse_expression(expression):
    elements = list(expression.split())
    if len(elements) != 3:
        raise Exception(f"Invalid expression '{expression}'. Three items required.")

    if elements[1] not in ["+", "-", "*", "/"]:
        raise Exception(f"Invalid expression '{expression}'. Operation must be '+' or '-' or '*' or '/'.")
    try:
        a = float(elements[0])
        b = float(elements[2])
    except ValueError:
        raise Exception(f"Invalid expression '{expression}'. Operands must be integers or floating point numbers.")
    op = elements[1]

    return a, b, op


def main():
    print("""
Welcome to the calculator powered by SingularityNET platform!
Please type the expression you want to calculate, e.g. 2 + 3.
Type 'exit' to exit the program.""")
    while True:
        expression = input("Calculator> ")
        if expression == "exit":
            break
        try:
            a, b, op = parse_expression(expression)
            print(f"Calculating {a} {op} {b}...")
            result = calc_client.call_rpc(operators[op], "Numbers", a=a, b=b)
            print(f"{a} {op} {b} = {result}")
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()

