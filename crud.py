from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from datetime import date, timedelta

router = APIRouter()

def get_db():
    """
    Dependency to get the database session.

    Yields:
        Session: SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/contacts/", response_model=schemas.ContactResponse)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    """
    Create a new contact.

    Args:
        contact (schemas.ContactCreate): Contact data to create.
        db (Session): Database session.

    Returns:
        schemas.ContactResponse: Created contact information.
    """
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/contacts/", response_model=list[schemas.ContactResponse])
def get_contacts(db: Session = Depends(get_db)):
    """
    Get all contacts.

    Args:
        db (Session): Database session.

    Returns:
        list[schemas.ContactResponse]: List of all contacts.
    """
    return db.query(models.Contact).all()

@router.get("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Get a contact by ID.

    Args:
        contact_id (int): ID of the contact.
        db (Session): Database session.

    Raises:
        HTTPException: If contact is not found.

    Returns:
        schemas.ContactResponse: Contact information.
    """
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def update_contact(contact_id: int, contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    """
    Update a contact by ID.

    Args:
        contact_id (int): ID of the contact.
        contact (schemas.ContactCreate): Updated contact data.
        db (Session): Database session.

    Raises:
        HTTPException: If contact is not found.

    Returns:
        schemas.ContactResponse: Updated contact information.
    """
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in contact.dict().items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Delete a contact by ID.

    Args:
        contact_id (int): ID of the contact.
        db (Session): Database session.

    Raises:
        HTTPException: If contact is not found.

    Returns:
        dict: Confirmation message.
    """
    db_contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(db_contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

@router.get("/contacts/upcoming-birthdays/", response_model=list[schemas.ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    """
    Get contacts with upcoming birthdays within the next week.

    Args:
        db (Session): Database session.

    Returns:
        list[schemas.ContactResponse]: List of contacts with upcoming birthdays.
    """
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(models.Contact).filter(models.Contact.birthday.between(today, next_week)).all()
