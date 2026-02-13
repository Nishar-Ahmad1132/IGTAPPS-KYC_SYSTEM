from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import User
from ..schemas import UserCreate
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["Users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Login schema
# -------------------------
class LoginRequest(BaseModel):
    email: str
    mobile: str

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()

    # 🔥 If user exists → treat as login
    if existing:
        return {
            "user_id": existing.id,
            "kyc_status": existing.kyc_status,
            "message": "User already exists"
        }

    new_user = User(**user.dict())

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "user_id": new_user.id,
        "kyc_status": new_user.kyc_status
    }




# -------------------------
# LOGIN ROUTE (🔥 ADD THIS)
# -------------------------
@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.email == data.email,
        User.mobile == data.mobile
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "kyc_status": user.kyc_status
    }

# ✅ ADD THIS ROUTE
@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "mobile": user.mobile,
        "pan_number": user.pan_number,
        "kyc_status": user.kyc_status
    }
