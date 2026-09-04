
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solcx import compile_standard, install_solc
from web3 import Web3
from app.config import settings


def deploy():
    # Install solc compiler
    print("Installing Solidity compiler...")
    install_solc("0.8.19")

    # Read the contract source
    contract_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "contracts", "FaceVerification.sol"
    )
    with open(contract_path, "r") as f:
        contract_source = f.read()

    # Compile
    print("Compiling FaceVerification.sol...")
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "FaceVerification.sol": {"content": contract_source}
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            },
        },
        solc_version="0.8.19",
    )

    # Extract ABI and bytecode
    contract_data = compiled["contracts"]["FaceVerification.sol"]["FaceVerification"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    # Save ABI for reference
    abi_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "contracts", "FaceVerification_abi.json"
    )
    with open(abi_path, "w") as f:
        json.dump(abi, f, indent=2)
    print(f"ABI saved to {abi_path}")

    # Connect to Sepolia
    print(f"Connecting to Sepolia via {settings.ETH_RPC_URL}...")
    w3 = Web3(Web3.HTTPProvider(settings.ETH_RPC_URL))
    if not w3.is_connected():
        print("ERROR: Cannot connect to Ethereum node!")
        sys.exit(1)

    chain_id = w3.eth.chain_id
    print(f"Connected! Chain ID: {chain_id}")

    account = Web3.to_checksum_address(settings.ETH_WALLET_ADDRESS)
    balance = w3.eth.get_balance(account)
    print(f"Wallet: {account}")
    print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")

    if balance == 0:
        print("ERROR: No ETH balance! Get test ETH from a Sepolia faucet.")
        sys.exit(1)

    # Deploy
    print("Deploying contract...")
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = w3.eth.get_transaction_count(account)
    txn = contract.constructor().build_transaction({
        "chainId": chain_id,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
        "nonce": nonce,
        "from": account,
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key=settings.ETH_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    print(f"Transaction sent: {tx_hash.hex()}")
    print("Waiting for deployment confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    if receipt.status != 1:
        print(f"ERROR: Deployment failed! Receipt: {receipt}")
        sys.exit(1)

    contract_address = receipt.contractAddress

    print()
    print("=" * 60)
    print("  CONTRACT DEPLOYED SUCCESSFULLY!")
    print("=" * 60)
    print(f"  Contract Address: {contract_address}")
    print(f"  Transaction:      {tx_hash.hex()}")
    print(f"  Block:            {receipt.blockNumber}")
    print(f"  Gas Used:         {receipt.gasUsed}")
    print()
    print(f"  Etherscan: https://sepolia.etherscan.io/address/{contract_address}")
    print()
    print("  Add this to your .env file:")
    print(f"  CONTRACT_ADDRESS={contract_address}")
    print("=" * 60)


if __name__ == "__main__":
    deploy()
