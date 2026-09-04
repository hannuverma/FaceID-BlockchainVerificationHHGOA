import requests
from serpapi import GoogleSearch

from app.config import settings
from app.models import SearchResult


def upload_image(image_bytes: bytes, filename: str = "face.jpg") -> str:
    """
    Upload image bytes to catbox.moe and return the public URL.
    """
    try:
        res = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (filename, image_bytes, "image/jpeg")}
        )
        res.raise_for_status()
        public_url = res.text.strip()
        if not public_url.startswith("http"):
            raise ValueError(f"Unexpected upload response: {public_url}")
        return public_url
    except Exception as e:
        raise RuntimeError(f"Failed to upload image for reverse search: {e}")


def reverse_image_search(image_bytes: bytes) -> list[SearchResult]:
    """
    Upload the face image and perform a reverse image search using
    SerpApi's Google Lens engine.

    Returns:
        List of SearchResult objects, prioritizing social media matches.
    """
    if not settings.SERPAPI_API_KEY:
        raise RuntimeError("SERPAPI_API_KEY not configured in .env")

    # Upload image to get a public URL
    print("Uploading image for reverse search...")
    public_url = upload_image(image_bytes)
    print(f"Image uploaded: {public_url}")

    # Query Google Lens via SerpApi
    params = {
        "engine": "google_lens",
        "url": public_url,
        "api_key": settings.SERPAPI_API_KEY
    }

    client = GoogleSearch(params)
    results = client.get_dict()

    if "error" in results:
        raise RuntimeError(f"SerpApi error: {results['error']}")

    visual_matches = results.get("visual_matches", [])
    if not visual_matches:
        raise RuntimeError("No visual matches found for this face.")

    # Separate social media matches from general matches
    social_matches: list[SearchResult] = []
    general_matches: list[SearchResult] = []

    for item in visual_matches:
        link = item.get("link", "")
        result = SearchResult(
            title=item.get("title"),
            url=link,
            thumbnail=item.get("thumbnail"),
            source=item.get("source")
        )

        if any(domain in link for domain in settings.TARGET_DOMAINS):
            social_matches.append(result)
        else:
            general_matches.append(result)

    # Prioritize social media matches, fall back to general
    matched = social_matches if social_matches else general_matches[:5]

    if not matched:
        raise RuntimeError("No matching web or social media results found.")

    print(f"Found {len(social_matches)} social media matches, "
          f"{len(general_matches)} general matches")

    return matched
