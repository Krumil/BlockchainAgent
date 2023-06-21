from web3 import Web3, Account
from hexbytes import HexBytes
import json


with open("contracts/uniswap/goerli.json") as f:
    uniswap_goerli_contract_abi = json.load(f)

with open("contracts/erc20.json") as f:
    erc20_standard_abi = json.load(f)


def check_balance(
    erc20_contract_address: str,
    private_keys: str,
    minimum_balance: int,
    web3: Web3,
):
    wallet_address = Web3.to_checksum_address(Account.from_key(private_keys).address)
    erc20_contract = web3.eth.contract(
        address=Web3.to_checksum_address(erc20_contract_address),
        abi=erc20_standard_abi,
    )
    balance = erc20_contract.functions.balanceOf(
        Web3.to_checksum_address(wallet_address)
    ).call()

    if balance >= minimum_balance:
        return True
    else:
        return False


def check_allowance(
    erc20_contract_address: str,
    spender_contract_address: str,
    private_keys: str,
    minimum_allowance: int,
    web3: Web3,
):
    wallet_address = Web3.to_checksum_address(Account.from_key(private_keys).address)
    erc20_contract = web3.eth.contract(
        address=Web3.to_checksum_address(erc20_contract_address),
        abi=erc20_standard_abi,
    )
    allowance = erc20_contract.functions.allowance(
        Web3.to_checksum_address(wallet_address),
        Web3.to_checksum_address(spender_contract_address),
    ).call()
    if allowance >= minimum_allowance:
        return True
    else:
        return False


def approve_token_transfer(
    erc20_contract_address: str,
    spender_address: str,
    amount_in_wei: int,
    private_keys: str,
    web3: Web3,
) -> HexBytes:
    from_address = Web3.to_checksum_address(Account.from_key(private_keys).address)
    erc20_contract = web3.eth.contract(
        address=Web3.to_checksum_address(erc20_contract_address),
        abi=erc20_standard_abi,
    )
    approve_txn = erc20_contract.functions.approve(
        spender_address,
        amount_in_wei,
    ).build_transaction(
        {
            "from": from_address,
            "nonce": web3.eth.get_transaction_count(from_address),
        }
    )

    signed_txn = web3.eth.account.sign_transaction(approve_txn, private_keys)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction sent with hash: {txn_hash.hex()}")
    return txn_hash


def execute_swap(
    token_in: str,
    token_out: str,
    amount_to_sell: int,
    slippage: float,
    uniswap_v3_router_address: str,
    private_keys: str,
    web3: Web3,
):
    wallet_address = Web3.to_checksum_address(Account.from_key(private_keys).address)
    uniswap_contract = web3.eth.contract(
        address=Web3.to_checksum_address(uniswap_v3_router_address),
        abi=uniswap_goerli_contract_abi,
    )
    current_gas_price = web3.eth.gas_price
    fee = 3000
    gas_limit = 2000000
    gas_max_priority = 10
    minimum_amount = 0

    txn_params = (
        Web3.to_checksum_address(token_in),
        Web3.to_checksum_address(token_out),
        fee,
        wallet_address,
        amount_to_sell,
        minimum_amount,
        0,
    )
    txn = uniswap_contract.functions.exactInputSingle(txn_params).build_transaction(
        {
            "from": wallet_address,
            "gas": gas_limit,
            "maxFeePerGas": web3.to_wei(2 * current_gas_price, "gwei"),
            "maxPriorityFeePerGas": web3.to_wei(2 * gas_max_priority, "gwei"),
            "nonce": web3.eth.get_transaction_count(wallet_address),
        }
    )

    signed_txn = web3.eth.account.sign_transaction(txn, private_keys)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction sent with hash: {txn_hash.hex()}")
    txn_receipt = web3.eth.wait_for_transaction_receipt(txn_hash, timeout=900)
    print(f'Transaction was mined in block: {txn_receipt["blockNumber"]}')
    return str(txn_hash.hex())
