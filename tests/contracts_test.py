import logging
import pytest
import asyncio
import kubernetes.client
from unittest.mock import MagicMock, patch

from k8s_chain_state.contracts import get_contracts
from k8s_chain_state import config
from k8s_chain_state.contracts import create_contract

from starknet_py.net.gateway_client import GatewayClient

from k8s_chain_state.crd import ContractSpec


@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_get_contracts(capfd):
    mock_custom_objects_api = MagicMock(spec=kubernetes.client.CustomObjectsApi)
    mock_custom_objects_api.list_namespaced_custom_object.return_value = {
        'items': [
            {
                'metadata': {'name': 'contract1'},
                'spec': {'chain': 'chain1', 'address': 'address1'}
            },
            {
                'metadata': {'name': 'contract2'},
                'spec': {'chain': 'chain2', 'address': 'address2'}
            },
        ]
    }
    with patch("kubernetes.client.CustomObjectsApi") as mock_custom_objects_api_cls:
        mock_custom_objects_api_cls.return_value = mock_custom_objects_api

        await get_contracts()

        captured_output = capfd.readouterr()

        # Check if the print statements are correct
        assert "contract1 {'chain': 'chain1', 'address': 'address1'}" in captured_output.out
        assert "contract2 {'chain': 'chain2', 'address': 'address2'}" in captured_output.out



@pytest.mark.asyncio
async def test_create_contract(caplog):
    caplog.set_level(logging.INFO)
    
    mock_custom_objects_api = MagicMock(spec=kubernetes.client.CustomObjectsApi)
    with patch("kubernetes.client.CustomObjectsApi") as mock_custom_objects_api_cls:
        mock_custom_objects_api_cls.return_value = mock_custom_objects_api

        mock_client = MagicMock(spec=GatewayClient)
        await create_contract(mock_client, "chain1", "contract1", "address1")

        mock_custom_objects_api.create_namespaced_custom_object.assert_called_once_with(
            config.group, config.version, config.namespace, config.plural, {
                "apiVersion": f"{config.group}/{config.version}",
                "kind": "Contract",
                "metadata": {
                    "name": "contract1"
                },
                "spec": ContractSpec(address="address1", chain="chain1").dict()
            }
        )

        assert f"Contract contract1 created" in caplog.text
