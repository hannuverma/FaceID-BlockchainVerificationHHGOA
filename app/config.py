import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    ETH_RPC_URL: str = os.getenv("ETH_RPC_URL", "")
    ETH_PRIVATE_KEY: str = os.getenv("ETH_PRIVATE_KEY", "")
    ETH_WALLET_ADDRESS: str = os.getenv("ETH_WALLET_ADDRESS", "")
    CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "")

    # Social media domains to prioritize in search results
    TARGET_DOMAINS: list[str] = [
        "twitter.com", "x.com", "instagram.com",
        "linkedin.com", "reddit.com", "facebook.com",
        "youtube.com"
    ]


settings = Settings()
