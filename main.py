import cv2
from deepface import DeepFace
import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

def capture_face(output_path: str = "input_face.jpg"):

    cap = cv2.VideoCapture(0)


    if not cap.isOpened():
        print("Error cam not found")
        return

    print("Cam found and active Press s to capture and q to quit")

    saved = False

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error frame not received")
            break

        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite(output_path, frame)
            print(f"Frame saved to {output_path}")
            saved = True
            break

    cap.release()
    cv2.destroyAllWindows()
    return saved

def extract_face(image_path : str="input_face.jpg", output_path: str = "face_extracted.jpg") -> str:

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    faces = DeepFace.extract_faces(
        img_path=image_path,
        enforce_detection=True,
        detector_backend="opencv"
    )

    primary_face = faces[0]["face"]
    bgr_face = cv2.cvtColor((primary_face * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, bgr_face)
    return output_path


def reverse_image_search(image_path: str = "face_extracted.jpg"):
    import requests
    
    api_key = os.getenv("SERPAPI_API_KEY")
    
    if not api_key:
        print("api key not found")
        return

    print("Uploading image to get a public URL for Google Lens...")
    try:
        with open(image_path, "rb") as f:
            upload_res = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f}
            )
        upload_res.raise_for_status()
        public_url = upload_res.text.strip()
        print(f"Image uploaded successfully: {public_url}")
    except Exception as e:
        print(f"Failed to upload image: {e}")
        return

    params = {
        "engine": "google_lens",
        "url": public_url,  # Must be a publicly accessible image URL
        "api_key": api_key
    }
    try:
        client = GoogleSearch(params)
    except Exception as e:
        print(f"Error {e}")
    results = client.get_dict()
    visual_matches = results.get("visual_matches", [])
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    # Filter for known social networks or return the top matched source
    target_domains = ["twitter.com", "x.com", "instagram.com", "linkedin.com", "reddit.com"]
    matched_post = None

    for item in visual_matches:

        link = item.get("link", "")
        if any(domain in link for domain in target_domains):

            matched_post = {
                "title": item.get("title"),
                "url": link,
                "thumbnail": item.get("thumbnail"),
                "source": item.get("source")
            }
            break

    if not matched_post and visual_matches:
        top_match = visual_matches[0]
        matched_post = {
            "title": top_match.get("title"),
            "url": top_match.get("link"),
            "thumbnail": top_match.get("thumbnail"),
            "source": top_match.get("source")
        }



    if not matched_post:
        raise RuntimeError("No matching web or social media results found.")
    return matched_post

print(reverse_image_search())