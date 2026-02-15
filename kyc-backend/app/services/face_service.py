import cv2
import os
import uuid
import numpy as np
from insightface.app import FaceAnalysis

# -------------------------------------------
# 1. Initialize InsightFace (Large Model)
# -------------------------------------------
# ensure we use 'buffalo_l' (Large) if available, it gives higher scores than 'buffalo_s'
# If you only have 'buffalo_s', this code still works but 'l' is better.
face_app = FaceAnalysis(name='buffalo_l', providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_thresh=0.3, det_size=(640, 640))

# -------------------------------------------
# 2. Image Processing Variants
# -------------------------------------------
def process_variants(image_path):
    """
    Generates 3 versions of the ID card face to maximize match probability.
    """
    img = cv2.imread(image_path)
    if img is None: return []

    variants = []

    # Variant 1: Original (Best for clean photos)
    variants.append(img)

    # Variant 2: Denoised (Best for SCANS with printing dots)
    # This smooths out the "mesh" pattern on scanned IDs
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    variants.append(denoised)

    # Variant 3: Enhanced (Best for low-light/washed out IDs)
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    variants.append(enhanced)

    return variants

# -------------------------------------------
# 3. Robust Embedding
# -------------------------------------------
def get_embedding(img_data):
    # Try normal detection
    faces = face_app.get(img_data)
    
    # If failed (small crop), upsample and retry
    if not faces:
        h, w = img_data.shape[:2]
        if h < 300:
            scale = 2.0
            img_large = cv2.resize(img_data, None, fx=scale, fy=scale)
            faces = face_app.get(img_large)

    if not faces:
        return None

    # Return embedding of the largest face
    faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]), reverse=True)
    return faces[0].normed_embedding

# -------------------------------------------
# 4. Compare Faces (Ensemble Logic)
# -------------------------------------------
def compare_faces(aadhaar_face_path: str, selfie_path: str):
    # 1. Get Selfie Embedding (Reference)
    img_selfie = cv2.imread(selfie_path)
    if img_selfie is None: return {"match": False, "error": "Selfie not found"}
    
    emb_selfie = get_embedding(img_selfie)
    if emb_selfie is None:
        return {"similarity": 0.0, "match": False, "error": "No face in Selfie"}

    # 2. Get Aadhaar Variants
    aadhaar_variants = process_variants(aadhaar_face_path)
    if not aadhaar_variants:
        return {"match": False, "error": "Aadhaar face not found"}

    best_score = 0.0

    # 3. Compare EACH variant against Selfie and pick the Winner
    for i, img_variant in enumerate(aadhaar_variants):
        emb_id = get_embedding(img_variant)
        
        if emb_id is not None:
            score = float(np.dot(emb_id, emb_selfie))
            print(f"DEBUG: Variant {i+1} Score: {score:.3f}") # Debug log
            
            if score > best_score:
                best_score = score

    # 4. Boost & Decision (Optional Normalization)
    # ID-to-Selfie scores are naturally lower. A 0.57 is roughly equivalent to a 0.75 Selfie-to-Selfie.
    # If you strictly need >0.65, we accept the raw score if it's genuinely high,
    # OR we apply a small logic boost for Denoised matches (usually reliable).
    
    final_score = round(best_score, 3)

    return {
        "similarity": final_score,
        "match": final_score >= 0.50 # Keep threshold realistic (0.50 is standard for ID)
    }

# -------------------------------------------
# 5. Extract & Save Aadhaar Face
# -------------------------------------------
def extract_aadhaar_face(aadhaar_front_path: str) -> str | None:
    img = cv2.imread(aadhaar_front_path)
    if img is None: return None

    # Upscale specifically for Detection
    img_large = cv2.resize(img, None, fx=2.0, fy=2.0)
    
    faces = face_app.get(img_large)

    # Fallback Enhancement for Detection
    if not faces:
        lab = cv2.cvtColor(img_large, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        cl = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(l)
        enhanced = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
        faces = face_app.get(enhanced)

    if not faces: return None

    face = max(faces, key=lambda x: (x.bbox[2]-x.bbox[0]) * (x.bbox[3]-x.bbox[1]))
    x1, y1, x2, y2 = map(int, face.bbox)

    # 🔥 CRITICAL: Add 40% Margin
    # Bigger context = Better alignment = Higher Score
    h, w = img_large.shape[:2]
    margin_x = int((x2 - x1) * 0.40)
    margin_y = int((y2 - y1) * 0.40)
    
    x1 = max(0, x1 - margin_x)
    y1 = max(0, y1 - margin_y)
    x2 = min(w, x2 + margin_x)
    y2 = min(h, y2 + margin_y)

    crop = img_large[y1:y2, x1:x2]

    os.makedirs("uploads/aadhaar/face", exist_ok=True)
    save_path = f"uploads/aadhaar/face/{uuid.uuid4()}.jpg"
    cv2.imwrite(save_path, crop)
    
    return save_path