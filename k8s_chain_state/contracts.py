import logging
import kubernetes
from k8s_chain_state import config
from k8s_chain_state.crd import ContractSpec, ContractState
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.proxy.proxy_check import OpenZeppelinProxyCheck

logger = logging.getLogger(__name__)

def init_starknet(network: str):
    return GatewayClient(net={
        'starknet-testnet': 'testnet',
        'starknet-mainnet': 'mainnet'
    }[network])

def update_status(name: str, namespace: str, state: ContractState, message: str):
    custom_object_api = kubernetes.client.CustomObjectsApi()
    custom_object_api.patch_namespaced_custom_object_status(
        group=config.group, version=config.version, namespace=namespace, plural=config.plural, name=name, body={
            "status": {
                "state": state,
                "message": message
            }
        }
    )


def update_class_hash(name: str, namespace: str, class_hash: str):
    custom_object_api = kubernetes.client.CustomObjectsApi()
    custom_object_api.patch_namespaced_custom_object(
        group=config.group, version=config.version, namespace=namespace, plural=config.plural, name=name, body={
            "spec": {
                "class_hash": class_hash
            }
        }
    )


def update_proxy_status(name: str, namespace: str, implem_hash: str):
    custom_object_api = kubernetes.client.CustomObjectsApi()
    custom_object_api.patch_namespaced_custom_object(
        group=config.group, version=config.version, namespace=namespace, plural=config.plural, name=name, body={
            "spec": {
                "implem_hash": implem_hash
            }
        }
    )

async def get_proxy_metadata(client: GatewayClient, contract_address: str):
    try:
        class_hash = await OpenZeppelinProxyCheck().implementation_hash(int(contract_address, 16), client)
        if class_hash:
            return True, hex(class_hash)
    except Exception:
        pass
    return False, None


async def get_contract_metadata(client: GatewayClient, contract_address: str):
    try:
        class_hash = hex(await client.get_class_hash_at(contract_address))
        return True, class_hash
    except Exception:
        return False, None


async def create_contract(client: GatewayClient, chain: str, name: str, address: str):
    custom_object_api = kubernetes.client.CustomObjectsApi()

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
        logger.info(f"Contract {name} created")
    except kubernetes.client.ApiException as e:
        logger.error(f"Error creating contract: {e}")
        return

    await update_contract(client, name, address)


async def update_contract(client: GatewayClient, name: str, address: str):
    _, class_hash = await get_contract_metadata(client, address)
    if class_hash:
        update_class_hash(name, config.namespace, class_hash)
        update_status(name, config.namespace, ContractState.DEPLOYED, "Contract was found on StarkNet")
    else:
        update_status(name, config.namespace, ContractState.PENDING, "Contract was not found")

    _, implem_hash = await get_proxy_metadata(client, address)
    if implem_hash:
        update_proxy_status(name, config.namespace, implem_hash)


async def get_contracts():
    custom_object_api = kubernetes.client.CustomObjectsApi()
    contracts = custom_object_api.list_namespaced_custom_object(
        group=config.group, version=config.version, namespace=config.namespace, plural=config.plural
    )
    for item in contracts['items']:
        print(item['metadata']['name'], item['spec'])
