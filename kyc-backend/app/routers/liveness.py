from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
import shutil

from ..database import SessionLocal
from ..models import LivenessLogs
from ..services.liveness_service import verify_action

router = APIRouter(prefix="/liveness", tags=["Liveness"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/step/{user_id}")
def liveness_step(
    user_id: int,
    action: str,
    frames: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    os.makedirs("uploads/liveness", exist_ok=True)
    frame_paths = []

    # Save frames
    for file in frames:
        path = f"uploads/liveness/{uuid.uuid4()}.jpg"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        frame_paths.append(path)

    # Run verification
    result = verify_action(frame_paths, action)

    # Delete temp frames (avoid memory leak)
    for path in frame_paths:
        if os.path.exists(path):
            os.remove(path)

    # Update DB
    log = db.query(LivenessLogs).filter(
        LivenessLogs.user_id == user_id
    ).first()

    if not log:
        log = LivenessLogs(
            user_id=user_id,
            blink_detected=False,
            head_turn_detected=False,
            status=False
        )
        db.add(log)

    if action == "blink":
        log.blink_detected = result["success"]

    if action in ["left", "right"]:
        if result["success"]:
            log.head_turn_detected = True

    # Final liveness status
    if log.blink_detected and log.head_turn_detected:
        log.status = True

    db.commit()

    return {
        "success": result["success"],
        "overall_status": log.status
    }
