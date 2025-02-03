from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Contact
from schemas import ContactCreate, ContactResponse
from datetime import datetime, timedelta

router = APIRouter(prefix="/contacts", tags=["Contacts"])

# 1. Создать новый контакт
@router.post("/", response_model=ContactResponse)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    new_contact = Contact(**contact.dict())
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

# 2. Получить список всех контактов
@router.get("/", response_model=list[ContactResponse])
def get_contacts(db: Session = Depends(get_db)):
    return db.query(Contact).all()

# 3. Получить один контакт по ID
@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return contact

# 4. Обновить контакт
@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, updated_contact: ContactCreate, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")

    for key, value in updated_contact.dict().items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact

# 5. Удалить контакт
@router.delete("/{contact_id}", response_model=dict)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")

    db.delete(contact)
    db.commit()
    return {"message": "Контакт удален"}

# 6. Поиск контактов по имени, фамилии или email
@router.get("/search/", response_model=list[ContactResponse])
def search_contacts(query: str, db: Session = Depends(get_db)):
    contacts = db.query(Contact).filter(
        (Contact.first_name.ilike(f"%{query}%")) |
        (Contact.last_name.ilike(f"%{query}%")) |
        (Contact.email.ilike(f"%{query}%"))
    ).all()
    return contacts

# 7. Получить список дней рождений на ближайшие 7 дней
@router.get("/birthdays/", response_model=list[ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        Contact.birthday.between(today, next_week)
    ).all()
    return contacts
