import argparse
import asyncio
import logging
import sys
from k8s_chain_state.contracts import create_contract, get_contracts, init_starknet
from kubernetes import config as k8s_config

from k8s_chain_state.crd import create_crd

logger = logging.getLogger(__name__)

def setup_logging():
    import sys
    import os

    logs = logging.getLogger()
    logs.setLevel(logging._nameToLevel[os.getenv('LOGLEVEL') or "INFO"])

    ch = logging.StreamHandler()
    ch.setStream(sys.stderr)
    logs.addHandler(ch)
    logs.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Manage contracts on StarkNet")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("crd", help="Create/update custom resource definition")

    contract_parser = subparsers.add_parser("contract", help="Create a contract")
    contract_parser.add_argument("chain", help="Chain name, starknet-testnet or starknet-mainnet")
    contract_parser.add_argument("name", help="Contract name")
    contract_parser.add_argument("address", help="Contract address")

    subparsers.add_parser("list", help="List contracts")

    args = parser.parse_args()


    loop = asyncio.get_event_loop()
    if args.command == "crd":
        create_crd()
    elif args.command == "contract":
        k8s_config.load_kube_config()
        loop.run_until_complete(create_contract(init_starknet(args.chain), args.chain, args.name, args.address))
    elif args.command == "list":
        k8s_config.load_kube_config()
        loop.run_until_complete(get_contracts())
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    main()
