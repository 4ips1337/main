from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Contact
from routes import get_current_user

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_contact(name: str, phone: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a new contact.

    Args:
        name (str): Name of the contact.
        phone (str): Phone number of the contact.
        db (Session): Database session.
        current_user: Current authenticated user.

    Returns:
        Contact: The newly created contact.

    Raises:
        HTTPException: If there is any error during the creation process.
    """
    new_contact = Contact(name=name, phone=phone, owner_id=current_user.id)
    db.add(new_contact)
    db.commit()
    return new_contact

@router.get("/")
def get_contacts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve all contacts for the current user.

    Args:
        db (Session): Database session.
        current_user: Current authenticated user.

    Returns:
        List[Contact]: List of contacts belonging to the current user.
    """
    return db.query(Contact).filter(Contact.owner_id == current_user.id).all()
