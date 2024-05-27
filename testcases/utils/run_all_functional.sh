#./packages/sdk/testcases/utils/reset_environment.sh

cd testcases/functional_tests
python test_sdk_client.py

python test_prepaid_payment.py
