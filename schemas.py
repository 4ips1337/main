from pydantic import BaseModel, EmailStr, Field
from datetime import date

class ContactCreate(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: str | None = None

class ContactResponse(ContactCreate):
    id: int

    class Config:
        from_attributes = True
