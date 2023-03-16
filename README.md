# k8s-chain-state

[![PyPI - Version](https://img.shields.io/pypi/v/k8s-chain-state.svg)](https://pypi.org/project/k8s-chain-state)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/k8s-chain-state.svg)](https://pypi.org/project/k8s-chain-state)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install k8s-chain-state
```

## Test

```sh
hatch run python k8s_chain_state/cli.py crd
hatch run python k8s_chain_state/cli.py contract starknet-testnet set-nft 0x05f9e1c4975b0f71f0b1af2b837166d321af1cdba5c30c09b0d4822b493f1347 0x43b591d86d4352decf085ebffc368c19234802ac88bf8a60312e287c28e476c
```

## License

`k8s-chain-state` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
