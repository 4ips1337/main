from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy import Column, Integer, String, Date, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr, Field
from datetime import date, timedelta


DATABASE_URL = "postgresql+psycopg://postgres:123456@localhost:32768/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    birthday = Column(Date, nullable=False)
    additional_info = Column(String, nullable=True)


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
        orm_mode = True


app = FastAPI()


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/contacts/", response_model=ContactResponse, status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/", response_model=list[ContactResponse])
def get_contacts(
    search: str | None = Query(None, description="Search by first name, last name, or email"),
    db: Session = Depends(get_db),
):
    query = db.query(Contact)
    if search:
        query = query.filter(
            (Contact.first_name.ilike(f"%{search}%")) |
            (Contact.last_name.ilike(f"%{search}%")) |
            (Contact.email.ilike(f"%{search}%"))
        )
    return query.all()

@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, updated_contact: ContactCreate, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for key, value in updated_contact.dict().items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact

@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return

@app.get("/contacts/upcoming-birthdays/", response_model=list[ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    today = date.today()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        func.extract('month', Contact.birthday) == today.month,
        func.extract('day', Contact.birthday) >= today.day,
    ).all()

    if today.month != next_week.month:
        contacts += db.query(Contact).filter(
            func.extract('month', Contact.birthday) == next_week.month,
            func.extract('day', Contact.birthday) <= next_week.day,
        ).all()

    return contacts