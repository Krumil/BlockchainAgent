from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from web3 import Web3, Account
from typing import Type, List, Dict
from hexbytes import HexBytes
from dotenv import load_dotenv
from time import time
import os
import json

load_dotenv()

uniswap_v3_router_address = os.environ["UNISWAP_ADDRESS_ON_GOERLI"]

with open("contracts/uniswap/goerli.json") as f:
    contract_abi = json.load(f)


class TransactionInput(BaseModel):
    to: str = Field()
    value: float = Field()


class ArbitrumTransactionTool(BaseTool):
    name = "ArbitrumTransaction"
    description = "Sends a transaction on the Arbitrum blockchain"
    args_schema: Type[BaseModel] = TransactionInput

    def _run(
        self, to: str, value: float, private_keys: str, rpc_url: str, chain_id: int
    ) -> str:
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_keys)

        transaction = {
            "from": account.address,
            "to": HexBytes(to),
            "value": int(value * 1e18),
            "gas": 21000,
            "gasPrice": web3.eth.gas_price,
            "nonce": web3.eth.get_transaction_count(account.address),
            "chainId": chain_id,
        }

        signed_txn = account.sign_transaction(transaction)
        transaction_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return str(transaction_hash.hex())

    async def _arun(
        self, to: str, value: float, private_keys: str, rpc_url: str, chain_id: int
    ) -> str:
        raise NotImplementedError("ArbitrumTransaction does not support async")


class SwapInput(BaseModel):
    token_in: str = Field()
    token_out: str = Field()
    amount_in: int = Field()
    amount_out_min: int = Field()


class UniswapV3SwapTool(BaseTool):
    name = "UniswapV3Swap"
    description = "Swaps tokens on Uniswap V3 on the Arbitrum blockchain"
    args_schema: Type[BaseModel] = SwapInput

    def _run(
        self,
        token_in: str,
        token_out: str,
        amount_to_sell: int,
        slippage: float,
        private_keys: str,
        rpc_url: str,
    ) -> str:
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_keys)
        wallet_address = Web3.to_checksum_address(account.address)
        current_gas_price = web3.eth.gas_price
        fee = 3000
        gas_limit = 2000000
        gas_max_priority = 10
        uniswap = web3.eth.contract(
            address=Web3.to_checksum_address(uniswap_v3_router_address),
            abi=contract_abi,
        )
        minimum_amount = calculate_minimum_amount(
            wallet_address,
            uniswap,
            amount_to_sell,
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            slippage,
        )

        # Build the transaction.
        txn_params = (
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            fee,
            wallet_address,
            amount_to_sell,
            minimum_amount,
            0,
        )
        txn = uniswap.functions.exactInputSingle(txn_params).build_transaction(
            {
                "from": wallet_address,
                "gas": int(gas_limit),
                "maxFeePerGas": current_gas_price,
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

    async def _arun(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out_min: int,
    ) -> str:
        raise NotImplementedError("UniswapV3Swap does not support async")


class TokenInput(BaseModel):
    token_name: str = Field()


class ContractAddressTool(BaseTool):
    name = "ContractAddress"
    description = "Finds the contract address for a given token"
    args_schema: Type[BaseModel] = TokenInput

    def _run(self, token_name: str, token_data: List) -> str:
        for token in token_data:
            if token["name"] == token_name or token["symbol"] == token_name:
                return token["address"]
        return "Token not found"

    async def _arun(self, token_name: str) -> str:
        raise NotImplementedError("ContractAddress does not support async")


def calculate_minimum_amount(
    address: str,
    router_contract,
    amount_in: int,
    token1_address: str,
    token2_address: str,
    slippage: float,
) -> float:
    amount_in = Web3.to_wei(amount_in, "ether")

    params = {
        "tokenIn": token1_address,
        "tokenOut": token2_address,
        "fee": 3000,  # This is the fee tier, it can be 500, 3000, or 10000 on Uniswap V3
        "recipient": address,  # Your address
        "amountIn": amount_in,
        "amountOutMinimum": 0,  # Accept any amount of token2
        "sqrtPriceLimitX96": 0,  # No price limit
    }
    amount_out = router_contract.functions.exactInputSingle(params).call()
    amount_out_minimum = amount_out * (1 - slippage)

    return amount_out_minimum
