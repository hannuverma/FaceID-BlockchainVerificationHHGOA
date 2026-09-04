# FaceID → Blockchain Verification Pipeline (HH Goa 2026)

This project is a complete end-to-end pipeline that takes a face scan as input, identifies matching social media content via live reverse image search, and creates a mathematically verifiable, tamper-evident record of those findings on the Ethereum blockchain.

Built for the **HH Goa 2026 Shortlisting Task 3**.

## 🚀 Pipeline Overview

1. **Face Identification (`app/face.py`)**: Captures an image from the webcam and uses `DeepFace` (OpenCV backend) to detect and extract the primary face.
2. **Reverse Image Search (`app/search.py`)**: Uploads the extracted face to a temporary public URL and queries Google Lens via SerpApi. The results are filtered to prioritize actual social media profiles (LinkedIn, Twitter, Reddit, Facebook, Instagram, etc.).
3. **Blockchain Anchor (`app/blockchain.py`)**: Creates a deterministic JSON representation of the search results and computes a SHA-256 hash (a unique digital fingerprint). This hash is then stored permanently on the Ethereum Sepolia testnet via a custom Solidity smart contract.
4. **Data Verification (`app/blockchain.py`)**: To prove the data hasn't been tampered with, the pipeline retrieves the stored hash from the smart contract, re-computes the hash of the local data, and ensures they match perfectly.

## 🛠️ Tech Stack & Blockchain Details

* **Face Detection**: `DeepFace`, `OpenCV`
* **Search Engine**: `SerpApi` (Google Lens)
* **Blockchain**: **Ethereum Sepolia Testnet**
* **Smart Contract**: Written in `Solidity` (0.8.19), deployed using `py-solc-x` and `web3.py`.
* **API Framework**: `FastAPI` (for modular pipeline architecture)
* **Package Manager**: `uv`

## ⚙️ How to Run the Pipeline

### 1. Setup Environment
Ensure you have Python 3.13+ installed. Clone the repository and install dependencies using `uv`:

```bash
uv pip install -r requirements.txt
```

### 2. Configure Credentials
Create a `.env` file in the root directory and add your keys (see `.env.example`):
```env
SERPAPI_API_KEY=your_serpapi_key
ETH_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_alchemy_key
ETH_PRIVATE_KEY=your_metamask_private_key
ETH_WALLET_ADDRESS=your_wallet_address
```

### 3. Deploy the Smart Contract (One-time setup)
Before running the pipeline, you must deploy the `FaceVerification.sol` contract to Sepolia. *Note: You need a small amount of Sepolia test ETH in your wallet to pay for gas.*

```bash
uv run python scripts/deploy_contract.py
```
*Take the resulting contract address and add it to your `.env` file as `CONTRACT_ADDRESS=0x...`*

### 4. Run the End-to-End CLI Pipeline
This is the main demonstration script. It will open your webcam (press 's' to capture), extract the face, search the web, anchor the data to Sepolia, and verify it.

```bash
uv run python scripts/cli_capture.py
```

*(Optional) You can also run the pipeline as a FastAPI REST server:*
```bash
uv run uvicorn app.main:app --reload
# Visit http://localhost:8000/docs to interact with the Swagger UI
```

## ⚠️ Known Limitations

1. **Testnet Volatility**: Because the project uses a live public testnet (Sepolia), transaction anchoring speed is dependent on network congestion. Sometimes it takes 15-30 seconds for a block to be mined.
2. **Reverse Search Dependency**: The accuracy of the social media matching relies heavily on Google Lens and SerpApi. If a person has no public web presence, the search stage will fail to find a match.
3. **Image Hosting**: The SerpApi Google Lens engine requires a publicly accessible URL to perform a search. Currently, the pipeline temporarily uploads the extracted face to `catbox.moe` to facilitate this. In a production environment, this would be replaced with a secure AWS S3 bucket.
