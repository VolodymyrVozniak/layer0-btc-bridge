"""Swap AVAX to BTC.b or BTC.b to AVAX on TraderJoe"""

import random

from src import trade_avax_to_btc, trade_btc_to_avax, sleeping


# In seconds
SLEEP_FROM = 100
SLEEP_TO   = 200

# All values in AVAX
AMOUNT_FROM = 12.8
AMOUNT_TO   = 13.4
MAX_GAS     = 0.017  # ~0.2$ for Avalanche fees

RANDOM_WALLETS = True  # Shuffle wallets
WALLETS_PATH   = "data/wallets.txt"  # Path for file with private keys


if __name__ == "__main__":
    response = int(input('''
Module:
1. trade_avax_to_btc
2. trade_btc_to_avax

Choose module: '''))

    with open(WALLETS_PATH, "r") as f:
        WALLETS = [row.strip() for row in f]

    if RANDOM_WALLETS:
        random.shuffle(WALLETS)

    for i, wallet in enumerate(WALLETS):
        if response == 1:
            trade_avax_to_btc(
                name=str(i),
                private_key=wallet,
                value=random.uniform(AMOUNT_FROM, AMOUNT_TO),
                max_gas=MAX_GAS
            )
        elif response == 2:
            trade_btc_to_avax(
                name=str(i),
                private_key=wallet,
                max_btc=0.01,
                max_gas=MAX_GAS
            )
        else:
            raise NotImplementedError

        sleeping(SLEEP_FROM, SLEEP_TO)
