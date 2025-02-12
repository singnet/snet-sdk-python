import time

from snet import sdk
from snet.sdk.training.responses import ModelStatus


PRIVATE_KEY = "YOUR_PRIVATE_KEY"
INFURA_KEY = "YOUR_INFURA_KEY"


def main():
    config = sdk.config.Config(private_key=PRIVATE_KEY,
                               eth_rpc_endpoint=f"https://sepolia.infura.io/v3/{INFURA_KEY}",
                               concurrency=False)

    org_id = "ORG_ID"
    service_id = "SERVICE_ID"
    group_name = "GROUP_NAME"

    snet_sdk = sdk.SnetSDK(config)
    service_client = snet_sdk.create_service_client(org_id=org_id,
                                                    service_id=service_id,
                                                    group_name=group_name)

    grpc_method_name = "tts"

    new_model_data = service_client.training.create_model("stt", "test_model")
    model_id = new_model_data.model_id
    model_status = new_model_data.status
    print(f"\nModel ID: {model_id}, model status: {model_status}")
    ...

    # method_metadata = service_client.training.get_method_metadata("", model_id)
    # print(f"\nMethod metadata:\n {method_metadata}")
    # ...

    validate_price = service_client.training.validate_model_price(model_id)
    print(f"\nValidate price: {validate_price}")
    ...

    # method_metadata = service_client.training.get_method_metadata(method_name, model_id)
    # method_metadata = service_client.training.get_method_metadata("stt")
    # print(f"\nMethod metadata:\n {method_metadata}")
    # ...

    zip_path = "C:/Users/Arondondon/Desktop/test_files/test_dataset.zip"
    model_status = service_client.training.upload_and_validate(model_id, zip_path, validate_price)
    print(f"\nModel status: {model_status}")
    ...

    models = [model for model in service_client.training.get_all_models() if model.model_id == model_id]
    status = models[0].status
    print(f"\nModel status: {status}")
    while status != ModelStatus.VALIDATED:
        time.sleep(1)
        models = [model for model in service_client.training.get_all_models() if model.model_id == model_id]
        status = models[0].status
        print(f"\nModel status: {status}")
        ...

    train_price = service_client.training.train_model_price(model_id)
    print(f"\nTrain price: {train_price}")
    ...

    model_status = service_client.training.train_model(model_id, train_price)
    print(f"\nModel status: {model_status}")
    ...

    models = [model for model in service_client.training.get_all_models() if model.model_id == model_id]
    status = models[0].status
    print(f"\nModel status: {status}")
    while status != ModelStatus.READY_TO_USE:
        time.sleep(1)
        models = [model for model in service_client.training.get_all_models() if model.model_id == model_id]
        status = models[0].status
        print(f"\nModel status: {status}")
        ...

    model_data = service_client.training.get_model(model_id)
    print(f"\nModel data: {model_data}")
    ...

    # model_data = service_client.training.update_model(model_id, description="lalala")
    # print(f"\nModel data: {model_data}")
    #
    # models = service_client.training.get_all_models()
    # print("\nModels:", *models, sep="\n")
    # ...

    # model_status = service_client.training.delete_model(model_id)
    # print(f"\nModel status: {model_status}")
    # ...


if __name__ == "__main__":
    main()
