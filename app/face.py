import cv2
import numpy as np
import tempfile
import os
from deepface import DeepFace

from app.models import FaceExtractionResult


def extract_face_from_bytes(image_bytes: bytes) -> tuple[bytes, str]:

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode the uploaded image.")

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir=".") as tmp:
        tmp_input_path = tmp.name
        cv2.imwrite(tmp_input_path, img)

    try:
        faces = DeepFace.extract_faces(
            img_path=tmp_input_path,
            enforce_detection=True,
            detector_backend="opencv"
        )
    except Exception as e:
        os.unlink(tmp_input_path)
        raise ValueError(f"Face detection failed: {e}")
    finally:
        if os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)

    if not faces:
        raise ValueError("No face detected in the image.")

    primary_face = faces[0]["face"]
    bgr_face = cv2.cvtColor((primary_face * 255).astype("uint8"), cv2.COLOR_RGB2BGR)

    face_output_path = os.path.join(".", "face_extracted.jpg")
    cv2.imwrite(face_output_path, bgr_face)

    _, face_buffer = cv2.imencode(".jpg", bgr_face)
    face_bytes = face_buffer.tobytes()

    return face_bytes, face_output_path


def capture_face_from_camera(output_path: str = "input_face.jpg") -> str | None:

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not found")
        return None

    print("Camera active — Press 's' to capture, 'q' to quit")

    saved_path = None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Frame not received")
            break

        cv2.imshow("Face Capture", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite(output_path, frame)
            print(f"Frame saved to {output_path}")
            saved_path = output_path
            break

    cap.release()
    cv2.destroyAllWindows()
    return saved_path
