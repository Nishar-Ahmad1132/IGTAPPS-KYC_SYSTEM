import cv2
import re
import numpy as np
from paddleocr import PaddleOCR
from rapidfuzz import fuzz
from rapidfuzz import fuzz   # ensure this is imported


ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

# -------------------------
# CONFIG
# -------------------------
OCR_CONF_THRESHOLD = 0.75
NAME_MATCH_THRESHOLD = 70


# -------------------------
# UTIL
# -------------------------
def mask_aadhaar(num):
    if not num:
        return None
    return "XXXX XXXX " + num[-4:]


def correct_digits(text):
    mapping = {'B': '8', 'O': '0', 'D': '0', 'S': '5', 'I': '1', 'L': '1', 'Z': '2'}
    return ''.join(mapping.get(c, c) for c in text)


# -------------------------
# MULTI PREPROCESS
# -------------------------
def preprocess_variants(image_path):
    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    if w < 1000:
        scale = 1000 / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale)

    thresh = cv2.adaptiveThreshold(gray, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    kernel = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
    sharp = cv2.filter2D(gray, -1, kernel)

    invert = cv2.bitwise_not(gray)

    return [gray, thresh, sharp, invert]


# -------------------------
# OCR RUN
# -------------------------
def run_ocr_multi(images):
    results = []
    for img in images:
        res = ocr.ocr(img, cls=True)
        if res and res[0]:
            results.append(res)
    return results


# -------------------------
# AADHAAR NUMBER EXTRACTION
# -------------------------
def extract_aadhaar_number_from_result(result):
    candidates = []

    for line in result[0]:
        text = line[1][0].upper()
        y = line[0][0][1]
        conf = line[1][1]

        # 1. Clean the text (Fix O->0, B->8)
        t = correct_digits(text)
        
        # 2. Extract ONLY the digits to count them
        #    This removes spaces, 'VID', 'Mobile', etc.
        digits_only = re.sub(r'\D', '', t) 

        # ----------------------------------------
        # ⛔ CRITICAL FIX: COUNT THE DIGITS
        # ----------------------------------------
        
        # If the line has 16 digits (VID), ignore it completely.
        if len(digits_only) >= 16:
            continue
            
        # If the line has 10 digits (Mobile Number), ignore it.
        if len(digits_only) == 10:
            continue

        # ----------------------------------------
        # ✅ ACCEPT ONLY 12 DIGITS (AADHAAR)
        # ----------------------------------------
        if len(digits_only) == 12:
            
            # Double check: Is it physically formatted like "XXXX XXXX XXXX"?
            # (Length of string roughly 14 chars)
            # This ensures we don't pick up random 12-digit barcodes.
            if len(t.replace(" ", "")) >= 12: 
                candidates.append({
                    "num": digits_only,
                    "score": conf, 
                    "y": y
                })

    # ----------------------------------------
    # SELECT BEST CANDIDATE
    # ----------------------------------------
    if not candidates:
        return None

    # Sort by Score (Confidence)
    candidates.sort(key=lambda x: x["score"], reverse=True)

    best = candidates[0]["num"]
    # Return formatted "1234 5678 9012"
    return f"{best[:4]} {best[4:8]} {best[8:]}"


# -------------------------
# DOB
# -------------------------
def extract_dob(text: str):
    text = text.replace("\n", " ")
    text_upper = text.upper()

    # -------------------------
    # 1️⃣ STRICT MATCH: DOB keyword
    # -------------------------
    match = re.search(
        r'(DOB|DATE OF BIRTH)[^\d]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        text_upper
    )
    if match:
        return match.group(2)

    # -------------------------
    # 2️⃣ REMOVE ISSUE DATE AREA
    # -------------------------
    text_clean = re.sub(
        r'(ISSUE DATE|ISSUED)[^\d]*\d{1,2}[/-]\d{1,2}[/-]\d{4}',
        '',
        text_upper
    )

    # -------------------------
    # 3️⃣ FIND ALL DATES
    # -------------------------
    dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', text_clean)

    if not dates:
        return None

    # -------------------------
    # 4️⃣ PICK VALID DOB (AGE CHECK)
    # -------------------------
    valid_dates = []

    for d in dates:
        try:
            day, month, year = map(int, re.split(r'[/-]', d))

            # ignore unrealistic years
            if 1900 <= year <= 2025:
                age = 2026 - year

                # realistic age (5 to 120)
                if 5 <= age <= 120:
                    valid_dates.append((d, year))
        except:
            continue

    if valid_dates:
        # pick oldest (DOB is earliest)
        valid_dates.sort(key=lambda x: x[1])
        return valid_dates[0][0]

    return None

def format_dob(dob):
    if not dob:
        return None

    parts = re.split(r'[/-]', dob)

    if len(parts) == 3:
        return f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"

    return dob


# -------------------------
# NAME (SMART)
# -------------------------
def extract_name(result):
    lines = []

    for line in result[0]:
        text = line[1][0].strip()
        conf = line[1][1]
        y = line[0][0][1]

        lines.append({
            "text": text,
            "conf": conf,
            "y": y
        })

    lines = sorted(lines, key=lambda x: x["y"])

    blacklist = [
        "government", "india", "unique", "authority",
        "uidai", "aadhaar", "dob", "male", "female",
        "address", "vid", "year", "birth",
        "mobile", "phone", "mera", "pehchan",
        "identification", "proof", "citizenship"
    ]

    candidates = []

    # -------------------------
    # Find DOB line
    # -------------------------
    dob_index = -1
    for i, l in enumerate(lines):
        t = l["text"].lower()

        if "dob" in t or re.search(r'\d{2}/\d{2}/\d{4}', t):
            dob_index = i
            break

    # -------------------------
    # Extract candidates
    # -------------------------
    for i, l in enumerate(lines):
        raw = l["text"]

        # remove special chars
        clean = re.sub(r'[^A-Za-z ]', '', raw).strip()
        words = clean.split()

        # -------------------------
        # HARD FILTERS
        # -------------------------
        if len(words) < 2 or len(words) > 3:
            continue

        if any(w.lower() in blacklist for w in words):
            continue

        if not all(w.isalpha() for w in words):
            continue

        if any(len(w) <= 2 for w in words):
            continue

        # ❌ remove slogan
        if fuzz.partial_ratio(clean.lower(), "mera aadhaar meri pehchan") > 80:
            continue

        # ❌ remove government
        if fuzz.partial_ratio(clean.lower(), "government of india") > 80:
            continue

        # ❌ remove mobile line
        if "mobile" in raw.lower():
            continue

        # -------------------------
        # SCORING
        # -------------------------
        score = 0

        # confidence
        score += l["conf"] * 2

        # word length quality
        avg_len = sum(len(w) for w in words) / len(words)
        if avg_len >= 4:
            score += 2

        # position (very important)
        if dob_index != -1:
            distance = abs(i - dob_index)

            if distance == 1:
                score += 5
            elif distance <= 3:
                score += 3

        # avoid header
        if i < 3:
            score -= 2

        candidates.append((score, clean.title()))

    # -------------------------
    # SELECT BEST
    # -------------------------
    if candidates:
        candidates.sort(reverse=True, key=lambda x: x[0])
        return candidates[0][1]

    return None



# -------------------------
# GENDER EXTRACTION
# -------------------------
def extract_gender(text: str):
    text_upper = text.upper()
    
    # Check FEMALE first because the word contains "MALE"
    if "FEMALE" in text_upper:
        return "FEMALE"
        
    # Use word boundary \b to ensure it matches exactly "MALE" and not a slice of something else
    elif re.search(r'\bMALE\b', text_upper):
        return "MALE"
        
    elif "TRANSGENDER" in text_upper:
        return "TRANSGENDER"
        
    return None

# -------------------------
# OCR ENGINE
# -------------------------
def extract_aadhaar_data(image_path):
    images = preprocess_variants(image_path)
    results = run_ocr_multi(images)

    best = None
    best_score = 0

    for res in results:
        text = " ".join([l[1][0] for l in res[0]])

        # aadhaar = extract_aadhaar(text)
        aadhaar = extract_aadhaar_number_from_result(res)

        name = extract_name(res)
        dob = extract_dob(text)
        dob = format_dob(dob)
        # 🔥 NEW: Extract gender
        gender = extract_gender(text)

        score = 0

        if aadhaar:
            score += 5   # most important
        if name:
            score += 3
        if dob:
            score += 2

        if score > best_score:
            best_score = score
            best = (aadhaar, name, dob, gender, res)

    if not best:
        return {"confidence": 0}
    aadhaar, name, dob, gender, res = best
    conf = sum([l[1][1] for l in res[0]]) / len(res[0])
    return {
        "name": name,
        "dob": dob,
        "gender": gender,
        "aadhaar_number": mask_aadhaar(aadhaar),
        "aadhaar_full": aadhaar,
        "confidence": round(conf, 2)
    }


def run_ocr(path):
    return extract_aadhaar_data(path)