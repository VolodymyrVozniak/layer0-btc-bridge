import time
import datetime

from web3 import Web3
from loguru import logger

from .utils import search_setting_data, transaction_verification
from .settings import SETTING_LIST, TRADERJOE, TRADERJOE_ABI


def trade_avax_to_btc(name, private_key, value, max_gas):
    log_name = f'TRADERJOE AVAX to BTC.b'

    avalanche_data = search_setting_data(chain='Avalanche', list=SETTING_LIST)
    if len(avalanche_data) == 0:
        logger.error(f'{name} | {log_name} | Error while finding information about avalanche_data')
        return
    else:
        avalanche_data = avalanche_data[0]

    RPC = avalanche_data['RPC']
    BTC = avalanche_data['BTC']
    BTC_ABI = avalanche_data['BTC_ABI']

    # Connect and check
    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 120}))
    if w3.is_connected() == True:
        account = w3.eth.account.from_key(private_key)
        address = account.address
        logger.success(f'{name} | {address} | {log_name} | Connected to Avalanche')
    else:
        logger.error(f'{name} | {log_name} | Failed connection to {RPC}')
        return

    # Chack balance
    contractBTC = w3.eth.contract(address=w3.to_checksum_address(BTC), abi=BTC_ABI)
    token_symbol_to = contractBTC.functions.symbol().call()
    token_decimals_to = contractBTC.functions.decimals().call()
    balance_of_token_to1 = contractBTC.functions.balanceOf(address).call()
    human_balance_to = balance_of_token_to1/ 10 ** token_decimals_to
    logger.info(f'{name} | {address} | {log_name} | {token_symbol_to} = {human_balance_to}, transfer sum')

    # SWAP
    deadline = datetime.datetime.now() + datetime.timedelta(minutes = 30)
    deadline = int(deadline.timestamp())

    amountOutMin = int(value - (value * 50) // 1000)
    try:
        contractTRADERJOE = w3.eth.contract(address=w3.to_checksum_address(TRADERJOE), abi=TRADERJOE_ABI)
        nonce = w3.eth.get_transaction_count(address)
        while True:
            gas = contractTRADERJOE.functions.swapExactNATIVEForTokens(
                amountOutMin,
                (
                [10],
                [2],
                ['0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7','0x152b9d0FdC40C096757F570A51E494bd4b943E50']
                ),
                address,
                deadline
                ).estimate_gas({'from': address, 'value': w3.to_wei(value, "ether") , 'nonce': nonce, })
            gas = gas * 1.2
            gas_price = w3.eth.gas_price
            txCost = gas * gas_price
            txCostInEther = w3.from_wei(txCost, "ether").real
            if txCostInEther < max_gas:
                logger.info(f'{name} | {address} | {log_name} | Gas cost SWAP {txCostInEther} AVAX')
                break
            else:
                logger.warning(f'{name} | {address} | {log_name} | Gas cost SWAP {txCostInEther} AVAX, > max_gas')


        transaction = contractTRADERJOE.functions.swapExactNATIVEForTokens(
            amountOutMin,
            (
            [10],
            [2],
            ['0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7','0x152b9d0FdC40C096757F570A51E494bd4b943E50']
            ),
            address,
            deadline
            ).build_transaction({
            'from': address,
            'value': w3.to_wei(value, "ether"),
            'gas': int(gas),
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce})
        
        signed_transaction = account.sign_transaction(transaction)
        transaction_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        logger.success(f'{name} | {address} | {log_name} | Sign SWAP {transaction_hash.hex()}')
        status = transaction_verification(name, transaction_hash, w3, "Avalanche", log_name=log_name, text=f'SWAP AVAX to BTC.b {value}', logger=logger)
        if status == False:
            logger.error(f'{name} | {address} | {log_name} | Error SWAP AVAX to BTC.b {value}')
            return
    except Exception as Ex:
        if "insufficient funds for gas * price + value" in str(Ex):
            logger.error(f'{name} | {address} | {log_name} | Insufficient funds for SWAP AVAX to BTC.b {value} \n {str(Ex)}')
        logger.error(f'{name} | {address} | {log_name} | Error SWAP AVAX to BTC.b {value} \n {str(Ex)}')
        return

    # Check balance on receiver
    try:
        lv_count = 0
        while lv_count <= 360:
            try:
                balance_of_token_to2 = contractBTC.functions.balanceOf(address).call()
            except Exception as Ex:
                logger.error(f'{name} | {address} | {log_name} | Error balanceOf, {Ex}')
                time.sleep(30)
                continue
            human_balance_to = balance_of_token_to2 / 10 ** token_decimals_to
            logger.info(f'{name} | {address} | {log_name} | {token_symbol_to} = {human_balance_to}') 
            if balance_of_token_to1 < balance_of_token_to2:
                logger.success(f'{name} | {address} | {log_name} | {token_symbol_to} = {human_balance_to}, SWAP is done') 
                return True
            lv_count += 1
            time.sleep(30)
        logger.error(f'{name} | {address} | {log_name} | {token_symbol_to} = {human_balance_to}, not receive SWAP') 
        return
    except Exception as Ex:
        logger.error(f'{name} | {address} | {log_name} | Error while checking BRIDGE amount {value} \n {str(Ex)}')
        return
    

def trade_btc_to_avax(name, private_key, max_btc, max_gas):  
    avalanche_data = search_setting_data(chain='Avalanche', list=SETTING_LIST)
    if len(avalanche_data) == 0:
        logger.error(f'{name} | {log_name} | Error while finding information about avalanche_data')
        return
    else:
        avalanche_data = avalanche_data[0]
    
    log_name = f'TRADERJOE BTC.b to AVAX'

    RPC = avalanche_data['RPC']
    BTC_FROM = avalanche_data['BTC']
    BTC_ABI_FROM = avalanche_data['BTC_ABI']

    # Connect and check
    w3_from = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 120}))
    if w3_from.is_connected() == True:
        account = w3_from.eth.account.from_key(private_key)
        address = account.address
        logger.success(f'{name} | {address} | {log_name} | Connected to Avalanche')
    else:
        logger.error(f'{name} | {log_name} | Failed connection to {RPC}')
        return
  
    # Get BTC
    contractBTC_from = w3_from.eth.contract(address=w3_from.to_checksum_address(BTC_FROM), abi=BTC_ABI_FROM)
    token_symbol_BTC_from = contractBTC_from.functions.symbol().call()
    token_decimals_BTC_from = contractBTC_from.functions.decimals().call()
    balance_of_token_BTC_from = contractBTC_from.functions.balanceOf(address).call()
    human_balance_BTC_from = balance_of_token_BTC_from/ 10 ** token_decimals_BTC_from
    logger.info(f'{name} | {address} | {log_name} | {token_symbol_BTC_from} = {human_balance_BTC_from}, Avalanche')

    # Check balance
    if human_balance_BTC_from == 0:
        logger.error(f'{name} | {address} | {log_name} | No tokens') 
        return
    if human_balance_BTC_from > max_btc:
        amountIn = int(max_btc * 10 ** token_decimals_BTC_from)
        amount = max_btc
    else:
        amountIn = balance_of_token_BTC_from
        amount = balance_of_token_BTC_from/ 10 ** token_decimals_BTC_from
    logger.info(f'{name} | {address} | {log_name} | SWAP {amount}')

    # APPROVE BTC
    try:
        nonce = w3_from.eth.get_transaction_count(address)
        while True:
            gas = contractBTC_from.functions.approve(w3_from.to_checksum_address(TRADERJOE), amountIn).estimate_gas({'from': address, 'nonce': nonce, })
            gas = gas * 1.2
            gas_price = w3_from.eth.gas_price
            txCost = gas * gas_price
            txCostInEther = w3_from.from_wei(txCost, "ether").real
            if txCostInEther < max_gas:
                logger.info(f'{name} | {address} | {log_name} | Gas cost on approve {txCostInEther}, Avalanche')
                break
            else:
                logger.warning(f'{name} | {address} | {log_name} | Gas cost on approve {txCostInEther}, Avalanche, > max_gas')
                time.sleep(30)

        transaction = contractBTC_from.functions.approve(w3_from.to_checksum_address(TRADERJOE), amountIn).build_transaction({
            'from': address,
            'value': 0,
            'gas': int(gas),
            'gasPrice': w3_from.eth.gas_price,
            'nonce': nonce})
        signed_transaction = account.sign_transaction(transaction)
        transaction_hash = w3_from.eth.send_raw_transaction(signed_transaction.rawTransaction)
        logger.success(f'{name} | {address} | {log_name} | Sign Approve {transaction_hash.hex()}')
        status = transaction_verification(name, transaction_hash, w3_from, "Avalanche", log_name=log_name, text=f'Approve {amount}, Avalanche', logger=logger)
        if status == False:
            logger.error(f'{name} | {address} | {log_name} | Error on Approve {amount}, Avalanche')
            return
    except Exception as Ex:
        if "insufficient funds for gas * price + value" in str(Ex):
            logger.error(f'{name} | {address} | {log_name} | Insufficient funds for Approve {amount}, Avalanche \n {str(Ex)}')
            return
        logger.error(f'{name} | {address} | {log_name} | Error Approve {amount}, Avalanche \n {str(Ex)}')
        return
    
    time.sleep(2)

    # SWAP
    deadline = datetime.datetime.now() + datetime.timedelta(minutes = 30)
    deadline = int(deadline.timestamp())
    try:
        contractTRADERJOE = w3_from.eth.contract(address=w3_from.to_checksum_address(TRADERJOE), abi=TRADERJOE_ABI)
        nonce = w3_from.eth.get_transaction_count(address)
        while True:
            gas = contractTRADERJOE.functions.swapExactTokensForNATIVESupportingFeeOnTransferTokens(
                amountIn,
                1,
                (
                [10],
                [2],
                ['0x152b9d0FdC40C096757F570A51E494bd4b943E50','0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7']
                ),
                address,
                deadline
                ).estimate_gas({'from': address, 'value': 0 , 'nonce': nonce, })
            gas = gas * 1.2
            gas_price = w3_from.eth.gas_price
            txCost = gas * gas_price
            txCostInEther = w3_from.from_wei(txCost, "ether").real
            if txCostInEther < max_gas:
                logger.info(f'{name} | {address} | {log_name} | Gas cost on SWAP {txCostInEther} AVAX')
                break
            else:
                logger.warning(f'{name} | {address} | {log_name} | Gas cost on SWAP {txCostInEther} AVAX, > max_gas')


        transaction = contractTRADERJOE.functions.swapExactTokensForNATIVESupportingFeeOnTransferTokens(
            amountIn,
            1,
            (
            [10],
            [2],
            ['0x152b9d0FdC40C096757F570A51E494bd4b943E50','0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7']
            ),
            address,
            deadline
            ).build_transaction({
            'from': address,
            'value': 0,
            'gas': int(gas),
            'gasPrice': w3_from.eth.gas_price,
            'nonce': nonce})
        
        signed_transaction = account.sign_transaction(transaction)
        transaction_hash = w3_from.eth.send_raw_transaction(signed_transaction.rawTransaction)
        logger.success(f'{name} | {address} | {log_name} | Sign SWAP {transaction_hash.hex()}')
        status = transaction_verification(name, transaction_hash, w3_from, "Avalanche", log_name=log_name, text=f'SWAP AVAX to BTC.b {amount}', logger=logger)
        if status == False:
            logger.error(f'{name} | {address} | {log_name} | Error SWAP BTC.b to AVAX {amount}')
            return
        return True
    except Exception as Ex:
        if "insufficient funds for gas * price + value" in str(Ex):
            logger.error(f'{name} | {address} | {log_name} | Insufficient funds for SWAP BTC.b to AVAX {amount} \n {str(Ex)}')
            return
        logger.error(f'{name} | {address} | {log_name} | Error SWAP BTC.b to AVAX {amount} \n {str(Ex)}')
        return
