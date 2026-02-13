from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    mobile = Column(String)
    pan_number = Column(String)
    kyc_status = Column(String, default="BASIC_SUBMITTED")
    created_at = Column(DateTime, default=datetime.utcnow)


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    aadhaar_front_path = Column(String)
    aadhaar_back_path = Column(String)
    aadhaar_face_path = Column(String, nullable=True)
    selfie_path = Column(String, nullable=True)

class OCRData(Base):
    __tablename__ = "ocr_data"

    user_id = Column(Integer, primary_key=True)
    aadhaar_number = Column(String)
    aadhaar_full = Column(String)
    name = Column(String)
    dob = Column(String)
    gender = Column(String)
    confidence_score = Column(Float)


class FaceVerification(Base):
    __tablename__ = "face_verification"

    user_id = Column(Integer, primary_key=True)
    similarity_score = Column(Float)
    match_status = Column(Boolean)


class LivenessLogs(Base):
    __tablename__ = "liveness_logs"

    user_id = Column(Integer, primary_key=True)
    blink_detected = Column(Boolean)
    head_turn_detected = Column(Boolean)
    status = Column(Boolean)
