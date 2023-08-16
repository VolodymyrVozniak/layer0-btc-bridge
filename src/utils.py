import time
import random

from tqdm import tqdm
from web3 import Web3

from .settings import EXPLORERS


def search_setting_data(chain, list):
    return [element for element in list if element['CHAIN'] == chain]


def transaction_verification(name, transaction_hash, w3: Web3, chain, log_name, text, logger):
    time.sleep(30)
    try:
        transaction_data = w3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
        if transaction_data.get('status') != None and transaction_data.get('status') == 1:
            logger.success(f'{name} | {transaction_data.get("from")} | {log_name} | Successful transaction for {text}')
            logger.info(f'{name} | {transaction_data.get("from")} | {log_name} | Check transaction: {EXPLORERS[chain]}/{transaction_hash.hex()}')
            return True
        else:
            logger.error(f'{name} | {transaction_data.get("from")} | {log_name} | Failed transaction for {text}')
            logger.info(f'{name} | {transaction_data.get("from")} | {log_name} | Check transaction: {EXPLORERS[chain]}/{transaction_hash.hex()}')
            return False
    except Exception as e:
        logger.error(f'{name} | {transaction_hash.hex()} | {log_name} | Failed transaction: {e} | {text}')
        return False


def sleeping(from_sleep, to_sleep):
    x = random.randint(from_sleep, to_sleep)
    for i in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        time.sleep(1)
