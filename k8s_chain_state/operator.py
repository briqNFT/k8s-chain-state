import logging
import kopf
import kubernetes
from kubernetes import config as k8s_config
from crd import ContractSpec
from k8s_chain_state import config
from k8s_chain_state.crd import ContractState
from starknet_py.net.gateway_client import GatewayClient


def update_status(name, namespace, state: ContractState, message):
    custom_object_api = kubernetes.client.CustomObjectsApi()
    body = {
        "status": {
            "state": state,
            "message": message
        }
    }
    custom_object_api.patch_namespaced_custom_object_status(
        group=config.group, version=config.version, namespace=namespace, plural=config.plural, name=name, body=body
    )


def init_starknet():
    return GatewayClient(net='testnet')


async def check_contract_state(starknet: GatewayClient, contract_address):
    try:
        await starknet.get_code(contract_address)
    except Exception:
        return False
    return True


@kopf.on.create(version=config.version, kind=config.kind)
async def create_contract(spec, name, namespace, logger, **kwargs):
    try:
        contract = ContractSpec(**spec)
    except ValueError as e:
        raise kopf.PermanentError(f"Invalid contract data for {name}: {e}")

    logger.info(f"Contract created: {name} ({contract.address}, {contract.class_hash})")
    update_status(name, namespace, ContractState.PENDING, "Contract was updated")

    sn = init_starknet()
    if (await check_contract_state(sn, contract.address)):
        update_status(name, namespace, ContractState.DEPLOYED, "Contract was found on StarkNet")
        ch = await sn.get_class_hash_at(contract.address)
        custom_object_api = kubernetes.client.CustomObjectsApi()
        custom_object_api.patch_namespaced_custom_object(
            group=config.group, version=config.version, namespace=namespace, plural=config.plural, name=name, body={
                "spec": {
                    "class_hash": hex(ch)
                }
            }
        )


@kopf.on.update(version=config.version, kind=config.kind)
async def update_contract(spec, name, namespace, logger, **kwargs):
    try:
        contract = ContractSpec(**spec)
    except ValueError as e:
        raise kopf.PermanentError(f"Invalid contract data for {name}: {e}")

    logger.info(f"Contract updated: {name} ({contract.address}, {contract.class_hash})")
    update_status(name, namespace, ContractState.PENDING, "Contract was updated")

    sn = init_starknet()
    if (await check_contract_state(sn, contract.address)):
        update_status(name, namespace, ContractState.DEPLOYED, "Contract was found on StarkNet")
        ch = await sn.get_class_hash_at(contract.address)
        custom_object_api = kubernetes.client.CustomObjectsApi()
        custom_object_api.patch_namespaced_custom_object(
            group=config.group, version=config.version, namespace=namespace, plural=config.plural, name=name, body={
                "spec": {
                    "class_hash": hex(ch)
                }
            }
        )

if __name__ == "__main__":
    k8s_config.load_kube_config()
    kopf.run(namespace="default")
