import cv2
import re
import numpy as np
from paddleocr import PaddleOCR

# Initialize Model (Load once)
ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

# --------------------------------------------------
# 1. UTILS
# --------------------------------------------------
def mask_aadhaar(num: str):
    if not num: return None
    return "XXXX XXXX " + num[-4:]

def clean_text(text):
    """Removes special characters to help regex matching."""
    return re.sub(r'[^A-Za-z0-9\s]', '', text).strip()

# --------------------------------------------------
# 2. PREPROCESSING (Dual-Pass Strategy)
# --------------------------------------------------
def get_processed_variants(image_path):
    """
    Returns TWO versions of the image:
    1. Grayscale (Best for clean digital scans like f1.jpg)
    2. Adaptive Threshold (Best for camera photos with shadows like b1.jpg)
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Image not found")
    
    # Resize to standard width (~1000px) for consistent OCR size
    h, w = img.shape[:2]
    if w < 1000:
        scale = 1000 / w
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Variant 1: Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Variant 2: Threshold (High Contrast)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return [gray, thresh]

# --------------------------------------------------
# 3. EXTRACTION LOGIC (The Brain)
# --------------------------------------------------

def extract_aadhaar_number(full_text):
    """
    Finds Aadhaar number even if spaces are missing.
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', full_text)
    
    # 1. Look for 12 continuous digits (Aadhaar never starts with 0 or 1 usually)
    # This handles '589518607018' (Merged)
    matches = re.findall(r'\b[2-9]\d{11}\b', digits_only)
    if matches:
        num = matches[0]
        return f"{num[:4]} {num[4:8]} {num[8:]}"

    # 2. Fallback: Look for standard format 'XXXX XXXX XXXX' in raw text
    match_space = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', full_text)
    if match_space:
        return match_space.group()

    return None

def extract_dob(lines):
    """
    Finds DOB. PRIORITIZES lines with 'DOB' label.
    IGNORES 'Issue Date' or 'Download Date'.
    """
    date_pattern = r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b'
    
    # Strategy 1: Look for "DOB" or "Birth" keyword (Most Accurate)
    for line in lines:
        text = line["text"]
        lower_text = text.lower()
        
        # ⛔ CRITICAL: Skip Issue/Download dates
        if "issue" in lower_text or "download" in lower_text:
            continue
            
        if "dob" in lower_text or "birth" in lower_text:
            match = re.search(date_pattern, text)
            if match:
                return match.group(1).replace('-', '/')

    # Strategy 2: If no label found, grab the first Valid Date that isn't Issue Date
    for line in lines:
        text = line["text"]
        lower_text = text.lower()
        
        if "issue" in lower_text or "download" in lower_text:
            continue
            
        match = re.search(date_pattern, text)
        if match:
            return match.group(1).replace('-', '/')
            
    # Strategy 3: Year only (YOB)
    for line in lines:
        if "year" in line["text"].lower() or "yob" in line["text"].lower():
            match = re.search(r'\b(\d{4})\b', line["text"])
            if match:
                return f"01/01/{match.group(1)}"

    return None

def extract_name(lines, dob_value):
    """
    Finds Name relative to DOB position.
    """
    # Find the Y-coordinate (vertical position) of the DOB line
    dob_y = -1
    for i, line in enumerate(lines):
        # Check if this line contains the extracted DOB value
        if dob_value and dob_value in line["text"].replace('-', '/'):
            dob_y = line["y"]
            break
        # Or if it has the label
        if "dob" in line["text"].lower() or "birth" in line["text"].lower():
            dob_y = line["y"]
            break

    # If we found DOB, look strictly ABOVE it
    if dob_y != -1:
        # Filter lines that are ABOVE the DOB line (smaller Y value)
        # We check lines within a reasonable distance (e.g., within 200px above)
        candidates = [l for l in lines if l["y"] < dob_y]
        
        # Sort candidates from Bottom-to-Top (closest to DOB first)
        candidates = sorted(candidates, key=lambda x: x["y"], reverse=True)
        
        for cand in candidates:
            text = cand["text"]
            clean = clean_text(text).lower()
            
            # ⛔ BLOCKLIST: Skip these
            if any(x in clean for x in ["government", "india", "father", "husband", "address", "uidai", "dob", "help", "www", "issue", "male", "female"]):
                continue
            
            # ⛔ Skip Hindi / Non-English
            if re.search(r'[^\x00-\x7F]+', text):
                continue

            # ⛔ Skip Numbers (Name shouldn't be digits)
            if re.search(r'\d', text):
                continue
                
            # If it passed all filters, it's the Name!
            if len(text) > 2:
                return text.title()
    
    return None

# --------------------------------------------------
# 4. MAIN CONTROLLER
# --------------------------------------------------
def extract_aadhaar_data(image_path):
    # 1. Get Image Variants (Gray & Threshold)
    variants = get_processed_variants(image_path)
    
    final_result = {
        "name": None, "dob": None, 
        "aadhaar_number": None, "aadhaar_full": None, 
        "confidence": 0.0
    }

    # 🔥 LOOP: Try Pass 1 (Gray), then Pass 2 (Threshold)
    for i, img in enumerate(variants):
        
        # Run PaddleOCR
        result = ocr.ocr(img, cls=True)
        if not result or not result[0]:
            continue
        
        # Organize Lines [ {text, y}, ... ]
        ocr_lines = []
        full_text_dump = ""
        
        for line in result[0]:
            text = line[1][0].strip()
            box = line[0]
            y_center = (box[0][1] + box[3][1]) / 2  # Calculate vertical center
            
            ocr_lines.append({"text": text, "y": y_center})
            full_text_dump += " " + text
        
        # Sort lines Top-to-Bottom (Crucial for logic)
        ocr_lines = sorted(ocr_lines, key=lambda x: x["y"])

        # --- EXTRACT FIELDS ---
        aadhaar = extract_aadhaar_number(full_text_dump)
        dob = extract_dob(ocr_lines)
        name = extract_name(ocr_lines, dob)

        # Save valid results
        if aadhaar: final_result["aadhaar_full"] = aadhaar
        if dob: final_result["dob"] = dob
        if name: final_result["name"] = name
        
        # ✅ EARLY EXIT: If we found everything, stop processing
        if final_result["aadhaar_full"] and final_result["name"] and final_result["dob"]:
            final_result["confidence"] = 0.95
            break

    # Final Formatting
    if final_result["aadhaar_full"]:
        final_result["aadhaar_number"] = mask_aadhaar(final_result["aadhaar_full"])
    else:
        final_result["confidence"] = 0.0

    return final_result

# Wrapper for API
def run_ocr(image_path):
    return extract_aadhaar_data(image_path)