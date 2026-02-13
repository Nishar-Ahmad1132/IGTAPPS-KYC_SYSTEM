from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile: str = Field(pattern=r"^\d{10}$")
    pan_number: str = Field(pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
