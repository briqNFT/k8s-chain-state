import sys
from typing import Optional
from pydantic import BaseModel
from kubernetes import client, config as k8s_config
from k8s_chain_state import config


from enum import Enum


class ContractState(str, Enum):
    PENDING = "Pending"
    DEPLOYED = "Deployed"
    FAILED_DEPLOYMENT = "FailedDeployment"


class ContractSpec(BaseModel):
    address: str
    class_hash: Optional[str] = None
    chain: str


def create_crd():
    k8s_config.load_kube_config()
    api_instance = client.ApiextensionsV1Api()

    crd = {
        "apiVersion": "apiextensions.k8s.io/v1",
        "kind": "CustomResourceDefinition",
        "metadata": {
            "name": f"{config.plural}.{config.group}"
        },
        "spec": {
            "group": config.group,
            "names": {
                "kind": config.kind,
                "listKind": config.list_kind,
                "plural": config.plural,
                "singular": config.singular
            },
            "scope": "Namespaced",
            "versions": [
                {
                    "name": config.version,
                    "served": True,
                    "storage": True,
                    "subresources": {
                        "status": {}
                    },
                    "schema": {
                        "openAPIV3Schema": {
                            "type": "object",
                            "properties": {
                                "spec": ContractSpec.schema(),
                                "status": {
                                    "type": "object",
                                    "properties": {
                                        "state": {
                                            "type": "string",
                                            "enum": [state.value for state in ContractState]
                                        },
                                        "message": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "additionalPrinterColumns": [
                        {
                            "name": "State",
                            "type": "string",
                            "jsonPath": ".status.state",
                            "description": "The current state of the contract"
                        },
                        {
                            "name": "Chain",
                            "type": "string",
                            "jsonPath": ".spec.chain",
                            "description": "The chain of the contract"
                        },
                        {
                            "name": "Address",
                            "type": "string",
                            "jsonPath": ".spec.address",
                            "description": "The address of the contract"
                        }
                    ]
                }
            ]
        }
    }

    try:
        api_instance.delete_custom_resource_definition(f"{config.plural}.{config.group}")
    except:
        pass

    try:
        api_instance.create_custom_resource_definition(crd)
        print("CustomResourceDefinition created")
    except client.ApiException as e:
        print(f"Error creating CustomResourceDefinition: {e}")
