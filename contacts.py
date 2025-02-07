from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Contact
from routes import get_current_user

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_contact(name: str, phone: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new_contact = Contact(name=name, phone=phone, owner_id=current_user.id)
    db.add(new_contact)
    db.commit()
    return new_contact

@router.get("/")
def get_contacts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Contact).filter(Contact.owner_id == current_user.id).all()
