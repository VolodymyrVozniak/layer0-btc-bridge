"""Bridge all BTC.b between Avalanche and Polygon using BTC Bridge"""

import random

from src import bridge_btc, sleeping


# In seconds
SLEEP_FROM = 100
SLEEP_TO   = 200

RANDOM_WALLETS = True  # Shuffle wallets
WALLETS_PATH   = "data/wallets.txt"  # Path for file with private keys


if __name__ == "__main__":
    response = int(input('''
Module:
1. Bridge from Avalanche to Polygon
2. Bridge from Polygon to Avalanche

Choose module: '''))

    with open(WALLETS_PATH, "r") as f:
        WALLETS = [row.strip() for row in f]

    if RANDOM_WALLETS:
        random.shuffle(WALLETS)

    for i, wallet in enumerate(WALLETS):
        if response == 1:
            bridge_btc(
                name=str(i),
                private_key=wallet,
                from_chain="Avalanche",
                to_chain="Polygon",
                max_bridge="ALL",
                max_gas=0.017,  # ~0.2$ for Avalanche fees
                max_value=0.08  # ~0.9$ for Layer0 fees
            )
        elif response == 2:
            bridge_btc(
                name=str(i),
                private_key=wallet,
                from_chain="Polygon",
                to_chain="Avalanche",
                max_bridge="ALL",
                max_gas=0.1,   # ~0.1$ for Polygon fees
                max_value=1.5  # ~0.9$ for Layer0 fees
            )
        else:
            raise NotImplementedError

        sleeping(SLEEP_FROM, SLEEP_TO)
