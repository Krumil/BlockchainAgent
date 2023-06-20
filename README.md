# LangChain Blockchain Tools

This repository contains a Python codebase for interacting with various blockchain tools. The main tools included are:

-   **ArbitrumTransactionTool**: This tool is used to send transactions on the Arbitrum blockchain.
-   **UniswapV3SwapTool**: This tool is used to execute swaps between two tokens on the Uniswap V3 platform.
-   **ContractAddressTool**: This tool is used to find the contract address for a given token.

## Setup

To use these tools, you need to have Python installed on your machine. You also need to install the necessary Python packages, which are listed in the `requirements.txt` file. You can install these packages using pip:

```bash
pip install -r requirements.txt
```

You also need to set up your environment variables. You can do this by creating a `.env` file in the root directory of the project, and adding the following variables:

```bash
OPENAI_API_KEY=your_openai_api_key
PRIVATE_KEYS=your_private_keys
ARBITRUM_TESTNET_RPC_URL=your_arbitrum_testnet_rpc_url
ARBITRUM_TESTNET_CHAIN_ID=your_arbitrum_testnet_chain_id
GOERLI_RPC_URL=your_goerli_rpc_url
UNISWAP_ADDRESS_ON_GOERLI=your_uniswap_address_on_goerli
```

Replace `your_openai_api_key`, `your_private_keys`, `your_arbitrum_testnet_rpc_url`, `your_arbitrum_testnet_chain_id`, `your_goerli_rpc_url`, and `your_uniswap_address_on_goerli` with your actual values.

## Usage

The main entry point of the application is `app.py`. This script initializes the tools and the OpenAI chat model, and then runs an example transaction.

To run the script, use the following command:

```bash
python app.py
```

I apologize for the confusion earlier. Here's the corrected version in Markdown syntax:

markdown
Copy code
Replace `your_openai_api_key`, `your_private_keys`, `your_arbitrum_testnet_rpc_url`, `your_arbitrum_testnet_chain_id`, `your_goerli_rpc_url`, and `your_uniswap_address_on_goerli` with your actual values.

## Usage

The main entry point of the application is `app.py`. This script initializes the tools and the OpenAI chat model, and then runs an example transaction.

To run the script, use the following command:

```bash
python app.py
```

You can modify the agent.run() command at the end of app.py to execute different transactions.
The input to this command should be a string representing the transaction you want to execute.
For example, to swap 0.000001 WETH for 0.000001 USDC with 10% of slippage, you would use:

```bash
agent.run("swap 0.000001 WETH for 0.000001 USDC with 10% slippage")
```

## Tools

The tools are defined in tools.py.
Each tool is a class that inherits from BaseTool, and implements a \_run() method that executes the tool's functionality.
The tools also define a \_arun() method for asynchronous execution, but this method is not currently implemented and will raise a NotImplementedError if called.

The ArbitrumTransactionTool and UniswapV3SwapTool tools require a private key and an RPC URL to interact with the blockchain.
These are provided through environment variables.

The ContractAddressTool tool requires a list of token data, which is loaded from a JSON file. The path to this file is hardcoded in app.py.

## Contributing

Contributions are welcome! Please submit a pull request or create an issue if you have any improvements or bug fixes.
