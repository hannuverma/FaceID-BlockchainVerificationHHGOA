from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    FaceExtractionResult,
    SearchResult,
    BlockchainRecord,
    VerificationResult,
    PipelineResult,
)
from app.face import extract_face_from_bytes
from app.search import reverse_image_search
from app.blockchain import (
    anchor_to_blockchain,
    verify_from_blockchain,
    compute_data_hash,
)

app = FastAPI(
    title="FaceID Blockchain Verification",
    description=(
        "A pipeline that takes a face scan as input, identifies matching "
        "content on the web/social media, and verifies that discovered data "
        "using a blockchain — end to end."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    from web3 import Web3

    status = {"api": "ok", "blockchain": "disconnected"}
    try:
        w3 = Web3(Web3.HTTPProvider(settings.ETH_RPC_URL))
        if w3.is_connected():
            status["blockchain"] = "connected"
            status["chain_id"] = w3.eth.chain_id
            status["latest_block"] = w3.eth.block_number
    except Exception:
        pass

    status["contract_address"] = settings.CONTRACT_ADDRESS or "NOT DEPLOYED"
    return status


@app.post("/face/extract", response_model=FaceExtractionResult)
async def extract_face(image: UploadFile = File(...)):

    try:
        image_bytes = await image.read()
        _, face_path = extract_face_from_bytes(image_bytes)
        return FaceExtractionResult(face_image_path=face_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face extraction failed: {e}")


@app.post("/search/reverse", response_model=list[SearchResult])
async def search_face(image: UploadFile = File(...)):

    try:
        image_bytes = await image.read()
        results = reverse_image_search(image_bytes)
        return results
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@app.post("/blockchain/anchor", response_model=BlockchainRecord)
async def anchor_data(search_results: list[SearchResult]):

    try:
        record = anchor_to_blockchain(search_results)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain anchor failed: {e}")


@app.post("/blockchain/verify/{record_id}", response_model=VerificationResult)
async def verify_data(record_id: int, search_results: list[SearchResult]):

    try:
        result = verify_from_blockchain(record_id, search_results)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {e}")


@app.post("/pipeline/run", response_model=PipelineResult)
async def run_pipeline(image: UploadFile = File(...)):

    try:
        image_bytes = await image.read()
        face_bytes, face_path = extract_face_from_bytes(image_bytes)
        face_result = FaceExtractionResult(face_image_path=face_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Face extraction: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face extraction: {e}")

    # Stage 2: Reverse image search
    try:
        search_results = reverse_image_search(face_bytes)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=f"Search: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search: {e}")

    # Stage 3: Anchor on blockchain
    try:
        blockchain_record = anchor_to_blockchain(search_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain anchor: {e}")

    # Stage 4: Immediate verification
    try:
        verification = verify_from_blockchain(
            blockchain_record.record_id, search_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification: {e}")

    return PipelineResult(
        face_extraction=face_result,
        search_results=search_results,
        blockchain_record=blockchain_record,
        verification=verification,
    )
