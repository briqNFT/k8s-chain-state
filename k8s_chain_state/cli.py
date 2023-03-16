import sys
from kubernetes import client, config as k8s_config
from k8s_chain_state.crd import ContractSpec, create_crd
from k8s_chain_state import config


def create_contract(chain: str, name: str, address: str):
    k8s_config.load_kube_config()

    custom_object_api = client.CustomObjectsApi()

    body = {
        "apiVersion": f"{config.group}/{config.version}",
        "kind": "Contract",
        "metadata": {
            "name": name
        },
        "spec": ContractSpec(address=address, chain=chain).dict()
    }

    try:
        custom_object_api.create_namespaced_custom_object(
            config.group, config.version, config.namespace, config.plural, body
        )
        print(f"Contract {name} created")
    except client.ApiException as e:
        print(f"Error creating contract: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python create_contract.py crd")
        print("  python create_contract.py contract <chain> <name> <address> <class_hash>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "crd":
        create_crd()
    elif command == "contract":
        if len(sys.argv) != 6:
            print("Usage:")
            print("  python create_contract.py contract<chain> <name> <address>")
            sys.exit(1)
        chain, name, address = sys.argv[2:5]
        create_contract(chain, name, address)
