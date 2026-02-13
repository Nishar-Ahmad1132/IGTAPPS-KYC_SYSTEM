import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import KYCDocument

router = APIRouter(prefix="/selfie", tags=["Selfie"])


# ---------------------------
# DB dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# Module 7: Capture selfie
# ---------------------------
@router.post("/capture/{user_id}")
def capture_selfie(
    user_id: int,
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Module 7:
    - Accept live webcam image
    - Save locally
    - Store path in DB
    """

    # ✅ create folder
    os.makedirs("uploads/selfie", exist_ok=True)

    filename = f"{uuid.uuid4()}.jpg"
    path = f"uploads/selfie/{filename}"

    # save file
    with open(path, "wb") as buffer:
        shutil.copyfileobj(selfie.file, buffer)

    # update latest document
    doc = (
        db.query(KYCDocument)
        .filter(KYCDocument.user_id == user_id)
        .order_by(KYCDocument.id.desc())
        .first()
    )

    if not doc:
        raise HTTPException(404, "Aadhaar not uploaded first")

    doc.selfie_path = path

    db.commit()

    return {
        "msg": "Selfie captured successfully",
        "selfie_path": path
    }
