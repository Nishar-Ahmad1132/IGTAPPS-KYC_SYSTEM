import cv2
import re
import os
from paddleocr import PaddleOCR
import numpy as np

# load model once (VERY IMPORTANT for performance)
ocr = PaddleOCR(use_angle_cls=True, lang="en")


# -------------------------
# mask aadhaar (security)
# -------------------------
def mask_aadhaar(num: str):
    if not num:
        return None
    return "XXXX XXXX " + num[-4:]


# -------------------------
# preprocess image
# -------------------------
# -------------------------
# preprocess image (MODULE 3 EXACT)
# -------------------------

def preprocess(img_path: str) -> str:
    img = cv2.imread(img_path)

    if img is None:
        raise ValueError("Image not found")

    # 1️⃣ grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2️⃣ resize (improves OCR clarity)
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # 3️⃣ gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 4️⃣ adaptive threshold
    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    # 5️⃣ sharpen (🔥 IMPORTANT for text edges)
    # 5️⃣ sharpen  (🔥 correct numpy kernel)
    kernel = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ], dtype=np.float32)

    sharpened = cv2.filter2D(thresh, -1, kernel)

    # 6️⃣ save to uploads/processed
    os.makedirs("uploads/processed", exist_ok=True)

    filename = os.path.basename(img_path)
    name, ext = os.path.splitext(filename)

    processed_path = f"uploads/processed/{name}_processed{ext}"

    cv2.imwrite(processed_path, sharpened)

    return processed_path

# Extract DOB using keywords and fallback
def extract_dob(text: str):
    # normalize text
    clean_text = text.replace("\n", " ").upper()

    # 🔥 find DOB using keyword
    dob_match = re.search(
        r'(DOB|DATE OF BIRTH)[^\d]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        clean_text
    )

    if dob_match:
        return dob_match.group(2)

    # fallback: pick oldest date (not issue date)
    dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', clean_text)

    if dates:
        # sort by year (smallest year = DOB)
        dates_sorted = sorted(dates, key=lambda d: int(d.split("/")[-1]))
        return dates_sorted[0]

    return None


def format_dob(dob):
    if not dob:
        return None
    parts = re.split(r'[/-]', dob)
    if len(parts) == 3:
        return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
    return dob


# -------------------------
# OCR extraction
# -------------------------
def extract_aadhaar_data(image_path: str) -> dict:
    processed = preprocess(image_path)

    result = ocr.ocr(processed)

    if not result or not result[0]:
        return {
            "raw_text": "",
            "aadhaar_number": None,
            "aadhaar_full": None,
            "name": None,
            "dob": None,
            "confidence": 0
        }

    text = ""
    confidence_sum = 0
    count = 0

    for line in result[0]:
        text_piece = line[1][0]
        conf = line[1][1]

        text += text_piece + " "
        confidence_sum += conf
        count += 1

    text = text.strip()
    avg_confidence = confidence_sum / count if count else 0

    aadhaar = re.search(r'\d{4}\s\d{4}\s\d{4}', text)
    # dob = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', text)
    dob = extract_dob(text)


    aadhaar_num = aadhaar.group() if aadhaar else None

    # 🔥 MODULE 5 NAME extraction
    words = text.split()
    name = None
    for i in range(len(words) - 1):
        if words[i].isalpha() and words[i+1].isalpha():
            name = words[i] + " " + words[i+1]
            break

    return {
        "raw_text": text,
        "aadhaar_number": mask_aadhaar(aadhaar_num),
        "aadhaar_full": aadhaar_num,   # unmasked full number
        "name": name,
        "dob": format_dob(dob),
        "confidence": round(avg_confidence, 2)
    }



# --------------------------------
# Public wrapper (called by router)
# --------------------------------
def run_ocr(image_path: str):
    return extract_aadhaar_data(image_path)
