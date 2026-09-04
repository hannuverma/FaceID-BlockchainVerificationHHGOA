from pydantic import BaseModel


class FaceExtractionResult(BaseModel):
    """Result of face extraction from an image."""
    face_image_path: str
    message: str = "Face extracted successfully"


class SearchResult(BaseModel):
    """A single search match from reverse image search."""
    title: str | None = None
    url: str | None = None
    thumbnail: str | None = None
    source: str | None = None


class BlockchainRecord(BaseModel):
    """Record of data anchored on the blockchain."""
    tx_hash: str
    record_id: int
    data_hash: str
    chain: str = "Ethereum Sepolia"
    etherscan_url: str | None = None


class VerificationResult(BaseModel):
    """Result of verifying data against the blockchain record."""
    is_verified: bool
    record_id: int
    on_chain_hash: str
    computed_hash: str
    message: str


class PipelineResult(BaseModel):
    """Full pipeline result combining all stages."""
    face_extraction: FaceExtractionResult
    search_results: list[SearchResult]
    blockchain_record: BlockchainRecord
    verification: VerificationResult
