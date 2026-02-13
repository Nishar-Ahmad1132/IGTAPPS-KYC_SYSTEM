import cv2
import os
import uuid
import numpy as np
from insightface.app import FaceAnalysis
from sklearn.metrics.pairwise import cosine_similarity


# Load InsightFace once (VERY IMPORTANT)
face_app = FaceAnalysis(providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0)


# -------------------------------------------
# Generate embedding from image
# -------------------------------------------
def get_embedding(image_path: str):
    img = cv2.imread(image_path)

    if img is None:
        return None

    faces = face_app.get(img)

    if not faces:
        return None

    # 🔥 USE NORMED EMBEDDING
    return faces[0].normed_embedding




# -------------------------------------------
# Compare Aadhaar face & selfie
# -------------------------------------------
def compare_faces(aadhaar_face_path: str, selfie_path: str):

    emb1 = get_embedding(aadhaar_face_path)
    emb2 = get_embedding(selfie_path)

    if emb1 is None or emb2 is None:
        return {
            "similarity": 0.0,
            "match": False
        }

    similarity = float(np.dot(emb1, emb2))  # cosine similarity directly

    return {
        "similarity": round(similarity, 3),
        "match": similarity >= 0.55
    }


# --------------------------------
# Haar face detector (OpenCV DNN alternative allowed)
# --------------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# --------------------------------
# MODULE 6: Aadhaar face extraction
# --------------------------------
def extract_aadhaar_face(aadhaar_front_path: str) -> str | None:
    img = cv2.imread(aadhaar_front_path)

    if img is None:
        return None

    # Resize full Aadhaar for better detection
    img_large = cv2.resize(img, None, fx=2.0, fy=2.0)

    faces = face_app.get(img_large)

    if not faces:
        print("No face detected in Aadhaar")
        return None

    face = faces[0]
    x1, y1, x2, y2 = map(int, face.bbox)

    # 🔥 Add margin (IMPORTANT)
    margin = 30
    x1 = max(0, x1 - margin)
    y1 = max(0, y1 - margin)
    x2 = min(img_large.shape[1], x2 + margin)
    y2 = min(img_large.shape[0], y2 + margin)

    crop = img_large[y1:y2, x1:x2]

    os.makedirs("uploads/aadhaar/face", exist_ok=True)

    face_path = f"uploads/aadhaar/face/{uuid.uuid4()}.jpg"
    cv2.imwrite(face_path, crop)

    return face_path
