from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from web3 import Web3, Account
from typing import Type, List, Dict
from hexbytes import HexBytes
from dotenv import load_dotenv
from time import time
from functions import (
    approve_token_transfer,
    check_allowance,
    check_balance,
    execute_swap,
)
import os
import json

load_dotenv()

arbitrum_rpc_url = os.environ["ARBITRUM_TESTNET_RPC_URL"]
arbitrum_chain_id = int(os.environ["ARBITRUM_TESTNET_CHAIN_ID"])
goerli_rpc_url = os.environ["GOERLI_RPC_URL"]
private_keys = os.environ["PRIVATE_KEYS"]
uniswap_v3_router_address = Web3.to_checksum_address(
    os.environ["UNISWAP_ADDRESS_ON_GOERLI"]
)

account = Account.from_key(private_keys)
wallet_address = Web3.to_checksum_address(account.address)


class TransactionInput(BaseModel):
    to: str = Field()
    value: float = Field()


class ArbitrumTransactionTool(BaseTool):
    name = "ArbitrumTransaction"
    description = "Sends a transaction on the Arbitrum blockchain"
    args_schema: Type[BaseModel] = TransactionInput

    def _run(self, to: str, value: float) -> str:
        web3 = Web3(Web3.HTTPProvider(arbitrum_rpc_url))

        transaction = {
            "from": account.address,
            "to": HexBytes(to),
            "value": int(value * 1e18),
            "gas": 21000,
            "gasPrice": web3.eth.gas_price,
            "nonce": web3.eth.get_transaction_count(account.address),
            "chainId": arbitrum_chain_id,
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
    ) -> str:
        web3 = Web3(Web3.HTTPProvider(goerli_rpc_url))

        if check_balance(token_in, private_keys, amount_to_sell, web3) == False:
            return "Insufficient balance"

        have_allowance = check_allowance(
            token_in,
            uniswap_v3_router_address,
            private_keys,
            amount_to_sell,
            web3,
        )

        if have_allowance == False:
            txn = approve_token_transfer(
                token_in,
                uniswap_v3_router_address,
                amount_to_sell,
                private_keys,
                web3,
            )
            web3.eth.wait_for_transaction_receipt(txn, timeout=900)

        swap_response = execute_swap(
            token_in,
            token_out,
            amount_to_sell,
            slippage,
            uniswap_v3_router_address,
            private_keys,
            web3,
        )
        return swap_response

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
