import hashlib
import json
from web3 import Web3

from app.config import settings
from app.models import BlockchainRecord, VerificationResult, SearchResult

CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "_dataHash", "type": "bytes32"}],
        "name": "storeRecord",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_id", "type": "uint256"}],
        "name": "getRecord",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_id", "type": "uint256"},
            {"internalType": "bytes32", "name": "_dataHash", "type": "bytes32"}
        ],
        "name": "verifyRecord",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "recordCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "id", "type": "uint256"},
            {"indexed": False, "internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "submitter", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "RecordStored",
        "type": "event"
    }
]


def _get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(settings.ETH_RPC_URL))
    if not w3.is_connected():
        raise ConnectionError(
            f"Cannot connect to ethereum node at {settings.ETH_RPC_URL}. "
            "Check your ETH_RPC_URL in .env"
        )
    return w3


def _get_contract(w3: Web3):
    if not settings.CONTRACT_ADDRESS:
        raise RuntimeError(
            "CONTRACT_ADDRESS not set in .env. "
            "Deploy the contract first using scripts/deploy_contract.py"
        )
    return w3.eth.contract(
        address=Web3.to_checksum_address(settings.CONTRACT_ADDRESS),
        abi=CONTRACT_ABI
    )


def compute_data_hash(search_results: list[SearchResult]) -> str:

    data = [result.model_dump() for result in search_results]
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)

    hash_bytes = hashlib.sha256(canonical.encode("utf-8")).digest()
    return "0x" + hash_bytes.hex()


def anchor_to_blockchain(search_results: list[SearchResult]) -> BlockchainRecord:

    w3 = _get_web3()
    contract = _get_contract(w3)

    data_hash_hex = compute_data_hash(search_results)
    data_hash_bytes32 = bytes.fromhex(data_hash_hex[2:])

    print(f"Data hash: {data_hash_hex}")
    print(f"Anchoring to Ethereum Sepolia...")

    account = Web3.to_checksum_address(settings.ETH_WALLET_ADDRESS)
    nonce = w3.eth.get_transaction_count(account)

    txn = contract.functions.storeRecord(data_hash_bytes32).build_transaction({
        "chainId": 11155111,  
        "gas": 200000,
        "gasPrice": w3.eth.gas_price,
        "nonce": nonce,
        "from": account,
    })

    signed_txn = w3.eth.account.sign_transaction(
        txn, private_key=settings.ETH_PRIVATE_KEY
    )
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_hash_hex = tx_hash.hex()

    print(f"Transaction sent: {tx_hash_hex}")
    print("Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt.status != 1:
        raise RuntimeError(f"Transaction failed! Receipt: {receipt}")

    record_id = 0
    logs = contract.events.RecordStored().process_receipt(receipt)
    if logs:
        record_id = logs[0]["args"]["id"]

    etherscan_url = f"https://sepolia.etherscan.io/tx/{tx_hash_hex}"
    print(f"Confirmed in block {receipt.blockNumber}")
    print(f"Etherscan: {etherscan_url}")

    return BlockchainRecord(
        tx_hash=tx_hash_hex,
        record_id=record_id,
        data_hash=data_hash_hex,
        etherscan_url=etherscan_url
    )


def verify_from_blockchain(
    record_id: int,
    search_results: list[SearchResult]
) -> VerificationResult:
    w3 = _get_web3()
    contract = _get_contract(w3)

    on_chain_hash_bytes, timestamp, submitter = contract.functions.getRecord(record_id).call()
    on_chain_hash = "0x" + on_chain_hash_bytes.hex()

    computed_hash = compute_data_hash(search_results)

    is_verified = on_chain_hash == computed_hash

    if is_verified:
        message = (
            f"VERIFIED: Data integrity confirmed. "
            f"The search results match the on-chain record #{record_id} "
            f"submitted by {submitter}."
        )
    else:
        message = (
            f"MISMATCH: Data has been tampered with! "
            f"On-chain hash: {on_chain_hash}, "
            f"Computed hash: {computed_hash}"
        )

    return VerificationResult(
        is_verified=is_verified,
        record_id=record_id,
        on_chain_hash=on_chain_hash,
        computed_hash=computed_hash,
        message=message
    )
