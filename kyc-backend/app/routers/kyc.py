from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
from fastapi import HTTPException



from fastapi import UploadFile, File
import uuid
import shutil
import os
from ..models import (
    User,
    KYCDocument,
    OCRData,
    FaceVerification,
    LivenessLogs
)

from ..database import SessionLocal

from ..services.face_service import compare_faces
from ..services.matching_service import match_names



router = APIRouter(prefix="/kyc", tags=["KYC"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================
# MODULE 9: FACE MATCHING
# =========================================

@router.post("/face-match/{user_id}")
def face_match(user_id: int, db: Session = Depends(get_db)):

    doc = db.query(KYCDocument).filter(
        KYCDocument.user_id == user_id
    ).order_by(KYCDocument.id.desc()).first()

    if not doc:
        raise HTTPException(status_code=404, detail="KYC documents not found")

    if not doc.aadhaar_face_path:
        raise HTTPException(status_code=400, detail="Aadhaar face not extracted")

    if not doc.selfie_path:
        raise HTTPException(status_code=400, detail="Selfie not found")

    result = compare_faces(
        doc.aadhaar_face_path,
        doc.selfie_path
    )

    # Save in face_verification table
    record = db.query(FaceVerification).filter(
        FaceVerification.user_id == user_id
    ).first()

    if not record:
        record = FaceVerification(user_id=user_id)

    record.similarity_score = result["similarity"]
    record.match_status = result["match"]

    db.add(record)

    # Optional: update user status
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.kyc_status = "FACE_VERIFIED" if result["match"] else "FACE_FAILED"

    db.commit()

    return {
        "similarity": result["similarity"],
        "match": result["match"]
    }



@router.post("/validate-name/{user_id}")
def validate_name(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    ocr = db.query(OCRData).filter(OCRData.user_id == user_id).first()

    if not user or not ocr:
        raise HTTPException(status_code=404, detail="Data not found")

    full_name = f"{user.first_name} {user.last_name}"

    result = match_names(full_name, ocr.name)

    # update status
    if result["match"]:
        user.kyc_status = "NAME_VERIFIED"
    else:
        user.kyc_status = "NAME_MISMATCH"

    db.commit()

    return result



# -------------------------------------------------
# MODULE 10: Final KYC Decision Engine
# -------------------------------------------------
@router.post("/final-decision/{user_id}")
def final_kyc_decision(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ocr = db.query(OCRData).filter(OCRData.user_id == user_id).first()
    face = db.query(FaceVerification).filter(
        FaceVerification.user_id == user_id
    ).first()
    liveness = db.query(LivenessLogs).filter(
        LivenessLogs.user_id == user_id
    ).first()

    # -----------------------------
    # OCR CHECK
    # -----------------------------
    ocr_success = (
        ocr is not None
        and ocr.confidence_score is not None
        and ocr.confidence_score >= 0.75
    )

    # -----------------------------
    # NAME MATCH CHECK
    # -----------------------------
    name_match = False
    if ocr and ocr.name:
        full_name = f"{user.first_name} {user.last_name}"
        name_result = match_names(full_name, ocr.name)
        name_match = name_result["match"]

    # -----------------------------
    # LIVENESS CHECK
    # -----------------------------
    liveness_passed = (
        liveness is not None
        and liveness.status is True
    )

    # -----------------------------
    # FACE MATCH CHECK
    # -----------------------------
    face_match = (
        face is not None
        and face.match_status is True
        and face.similarity_score >= 0.50
    )

    # -----------------------------
    # FINAL DECISION
    # -----------------------------
    if all([ocr_success, name_match, liveness_passed, face_match]):
        user.kyc_status = "VERIFIED"
        decision = "VERIFIED"
    else:
        user.kyc_status = "FAILED"
        decision = "FAILED"

    db.commit()

    print("---- FINAL KYC DEBUG ----")
    print("OCR SUCCESS:", ocr_success)
    print("NAME MATCH:", name_match)
    print("LIVENESS PASSED:", liveness_passed)
    print("FACE MATCH:", face_match)

    return {
        "user_id": user_id,
        "ocr_success": ocr_success,
        "name_match": name_match,
        "liveness_passed": liveness_passed,
        "face_match": face_match,
        "final_status": decision
    }


# =========================================
# CHECK CURRENT STATUS
# =========================================
@router.get("/status/{user_id}")
def get_status(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "kyc_status": user.kyc_status
    }

@router.get("/ocr/{user_id}")
def get_ocr(user_id: int, db: Session = Depends(get_db)):
    ocr = db.query(OCRData).filter(OCRData.user_id == user_id).first()

    if not ocr:
        raise HTTPException(status_code=404, detail="OCR not found")

    return {
        "name": ocr.name,
        "dob": ocr.dob,
        "aadhaar_number": ocr.aadhaar_number,   # masked
        "aadhaar_full": ocr.aadhaar_full,       # optional if stored
        "confidence": ocr.confidence_score
    }