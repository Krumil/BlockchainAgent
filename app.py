from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from tools import ArbitrumTransactionTool, UniswapV3SwapTool, ContractAddressTool
from dotenv import load_dotenv
import os
import json

load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]
private_keys = os.environ["PRIVATE_KEYS"]
arbitrum_rpc_url = os.environ["ARBITRUM_TESTNET_RPC_URL"]
arbitrum_chain_id = os.environ["ARBITRUM_TESTNET_CHAIN_ID"]
arbitrum_chain_id_int = int(arbitrum_chain_id)
goerli_rpc_url = os.environ["GOERLI_RPC_URL"]

arbitrum_tool = ArbitrumTransactionTool()
uniswap_tool = UniswapV3SwapTool()
contract_address_tool = ContractAddressTool()


def run_arbitrum_tool(to: str, value: float):
    return arbitrum_tool._run(
        to, value, private_keys, arbitrum_rpc_url, arbitrum_chain_id_int
    )


def parsing_arbitrum_tool(string: str):
    to, value = string.split(",")
    return run_arbitrum_tool(to, float(value))


def run_uniswap_tool(
    token_in: str,
    token_out: str,
    amount_in: int,
    slippage: float,
):
    return uniswap_tool._run(
        token_in,
        token_out,
        amount_in,
        slippage,
        private_keys,
        goerli_rpc_url,
    )


def parsing_uniswap_tool(string: str):
    token_in, token_out, amount_in, slippage = string.split(",")
    return run_uniswap_tool(token_in, token_out, int(amount_in), float(slippage))


def run_contract_address_tool(token_name: str):
    token_data = json.load(open("utilities/goerli/tokens.json"))
    return contract_address_tool._run(token_name, token_data)


tool = Tool(
    name="ArbitrumTransaction",
    func=parsing_arbitrum_tool,
    description="Sends a transaction on the Arbitrum blockchain. The input to this tool should be a comma separated list of strings of length two, representing the to address and the value to send. For example '0x8e5e01dca1706f9df683c53a6fc9d4bb8d237153,0.0000001' if you want to send 0.0000001 ETH to 0x8e5e01dca1706f9df683c53a6fc9d4bb8d237153.",
)
tool2 = Tool(
    name="UniswapV3Swap",
    func=parsing_uniswap_tool,
    description="Execute a blockchain swap between two tokens. The input to this tool should be a comma separated list of strings of length four, representing the address of the token in input, the address of the token in output, the amount of token in input and the slippage. For example '0x8e5e01dca1706f9df683c53a6fc9d4bb8d237153,0x8e5e01dca1706f9df683c53a6fc9d4bb8d237153,1000000000000000000,0.01' if you want to swap 1 token in input with 1% of slippage.",
)
tool3 = Tool(
    name="ContractAddress",
    func=run_contract_address_tool,
    description="Get the address of a token. The input to this tool should be a string representing the name of the token. For example 'USDC' if you want to get the address of the USDC token.",
)

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613", client=None)

agent = initialize_agent(
    [tool, tool2, tool3], llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True
)

agent.run("Swap 0.000001 WETH for 0.000001 USDC with 10% of slippage.")
