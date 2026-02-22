import uuid
import shutil
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import KYCDocument, OCRData
from ..services.ocr_service import run_ocr

from ..services.face_service import extract_aadhaar_face


router = APIRouter(prefix="/upload", tags=["Upload"])


# -------------------------
# DB dependency
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# File validation (MANDATORY)
# -------------------------
def validate_file(file: UploadFile):
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Only JPG/PNG allowed")

    file.file.seek(0, 2)
    size = file.file.tell()

    if size > 5 * 1024 * 1024:
        raise HTTPException(400, "Max size 5MB exceeded")

    file.file.seek(0)


# -------------------------
# Save file (UUID based)
# -------------------------
def save_file(file: UploadFile, folder: str):
    os.makedirs(f"uploads/{folder}", exist_ok=True)

    filename = f"{uuid.uuid4()}.jpg"
    path = f"uploads/{folder}/{filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return path


# -------------------------
# Upload Aadhaar
# -------------------------
@router.post("/aadhaar/{user_id}")
def upload_aadhaar(
    user_id: int,
    front: UploadFile = File(...),
    back: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # 🔥 VALIDATION (Module 2 requirement)
    validate_file(front)
    validate_file(back)

    # Save files
    front_path = save_file(front, "aadhaar/front")
    back_path = save_file(back, "aadhaar/back")
    # 🔥 MODULE 6 integration
    face_path = extract_aadhaar_face(front_path)

    # -------------------------
    # Save document paths
    # -------------------------
    doc = KYCDocument(
        user_id=user_id,
        aadhaar_front_path=front_path,
        aadhaar_back_path=back_path,
        aadhaar_face_path=face_path  # filled in Module 6 later
    )
    print("Saved Aadhaar Face Path:", doc.aadhaar_face_path)

    db.add(doc)
    # -------------------------
    # OCR (Module 3 + 4)
    # -------------------------
    ocr_result = run_ocr(front_path)


    # -------------------------
    # Save OCR data
    # -------------------------
    existing = db.query(OCRData).filter(OCRData.user_id == user_id).first()

    if existing:
        existing.aadhaar_number = ocr_result["aadhaar_number"]
        existing.name = ocr_result["name"]
        existing.dob = ocr_result["dob"]
        existing.gender = ocr_result["gender"]
        existing.confidence_score = ocr_result["confidence"]
    else:
        ocr_data = OCRData(
            user_id=user_id,
            aadhaar_number=ocr_result["aadhaar_number"],
            aadhaar_full=ocr_result["aadhaar_full"],      # full
            name=ocr_result["name"],   # 🔥 added
            dob=ocr_result["dob"],
            gender=ocr_result["gender"],
            confidence_score=ocr_result["confidence"]
        )
        db.add(ocr_data)

    db.commit()

    return {
        "msg": "Aadhaar uploaded & OCR processed",
        "ocr_result": ocr_result
    }
