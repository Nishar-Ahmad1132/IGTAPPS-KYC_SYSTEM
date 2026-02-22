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
# -------------------------------------------------
# MODULE 10: Final KYC Decision Engine (Updated)
# -------------------------------------------------
@router.post("/final-decision/{user_id}")
def final_kyc_decision(user_id: int, db: Session = Depends(get_db)):

    # 1. Fetch Records
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ocr = db.query(OCRData).filter(OCRData.user_id == user_id).first()
    face = db.query(FaceVerification).filter(FaceVerification.user_id == user_id).first()
    liveness = db.query(LivenessLogs).filter(LivenessLogs.user_id == user_id).first()

    # 2. Evaluate Individual Modules
    
    # A. OCR Status
    ocr_passed = (
        ocr is not None 
        and ocr.confidence_score is not None 
        and ocr.confidence_score >= 0.75
    )

    # B. Liveness Status
    liveness_passed = (
        liveness is not None 
        and liveness.status is True
    )

    # C. Name Match (Get Score)
    name_passed = False
    name_score = 0
    if ocr and ocr.name:
        full_name = f"{user.first_name} {user.last_name}"
        # We calculate exact score here to be sure
        name_score = fuzz.token_sort_ratio(full_name.lower(), ocr.name.lower())
        name_passed = name_score >= 80  # Strict name match

    # D. Face Match (Get Score)
    face_score = 0.0
    if face and face.similarity_score:
        face_score = float(face.similarity_score)

    # 3. THE DECISION MATRIX (Logic Core)
    
    final_status = "FAILED"
    reason = "Unknown"

    # CRITICAL: OCR, Liveness, and Name MUST pass for any approval
    if ocr_passed and liveness_passed and name_passed:
        
        # Scenario 1: Perfect Match (Auto-Verify)
        if face_score >= 0.50:  # Standard threshold
            final_status = "VERIFIED"
            reason = "Auto-Verified: High Match"

        # Scenario 2: "Child Photo" Case (Manual Review)
        # Name is correct, User is alive, but Face match is low (0.20 - 0.40)
        elif 0.30 <= face_score < 0.50:
            final_status = "MANUAL_REVIEW"
            reason = "Flagged: Name matched but Face score low (Old Photo?)"
        
        # Scenario 3: Face completely different
        else:
            final_status = "FAILED"
            reason = "Face Mismatch"

    else:
        # Failure Reasons
        if not ocr_passed: reason = "OCR Failed"
        elif not liveness_passed: reason = "Liveness Failed"
        elif not name_passed: reason = "Name Mismatch"

    # 4. Save & Return
    user.kyc_status = final_status
    db.commit()

    print("---- FINAL DECISION DEBUG ----")
    print(f"User: {user_id} | Status: {final_status}")
    print(f"Scores -> Name: {name_score}% | Face: {face_score}")
    print(f"Reason: {reason}")

    return {
        "user_id": user_id,
        "final_status": final_status,
        "reason": reason,
        "metrics": {
            "ocr_passed": ocr_passed,
            "liveness_passed": liveness_passed,
            "name_score": name_score,
            "face_score": face_score
        }
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