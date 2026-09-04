"""
CLI tool to capture a face from webcam and run the full pipeline.

Usage:
    uv run python scripts/cli_capture.py
"""
import os
import sys
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.face import capture_face_from_camera, extract_face_from_bytes
from app.search import reverse_image_search
from app.blockchain import anchor_to_blockchain, verify_from_blockchain


def main():
    print("=" * 50)
    print("  FaceID Blockchain Verification - CLI")
    print("=" * 50)
    print()

    # Step 1: Capture from camera
    print("[1/4] Capturing face from camera...")
    saved_path = capture_face_from_camera("input_face.jpg")
    if not saved_path:
        print("Capture cancelled.")
        return

    # Step 2: Extract face
    print("\n[2/4] Extracting face...")
    with open(saved_path, "rb") as f:
        image_bytes = f.read()
    face_bytes, face_path = extract_face_from_bytes(image_bytes)
    print(f"Face extracted to: {face_path}")

    # Step 3: Reverse image search
    print("\n[3/4] Searching the web for matching content...")
    search_results = reverse_image_search(face_bytes)
    print(f"\nFound {len(search_results)} matches:")
    for i, result in enumerate(search_results, 1):
        print(f"  {i}. [{result.source}] {result.title}")
        print(f"     {result.url}")

    # Step 4: Anchor on blockchain
    print("\n[4/4] Anchoring results on Ethereum Sepolia...")
    record = anchor_to_blockchain(search_results)
    print(f"\n  Transaction: {record.tx_hash}")
    print(f"  Record ID:   {record.record_id}")
    print(f"  Data Hash:   {record.data_hash}")
    print(f"  Etherscan:   {record.etherscan_url}")

    # Verify
    print("\nVerifying on-chain record...")
    verification = verify_from_blockchain(record.record_id, search_results)
    print(f"  Result: {verification.message}")

    print("\n" + "=" * 50)
    print("  Pipeline complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
