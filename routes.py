from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import User, Contact
from auth import (
    hash_password, verify_password, 
    create_access_token, create_refresh_token, decode_token
)
from schemas import UserCreate, UserLogin, TokenResponse, ContactCreate, ContactResponse
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from fastapi_limiter.depends import RateLimiter
from fastapi.middleware.cors import CORSMiddleware
import redis
import cloudinary
import cloudinary.uploader
from config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Setting up Redis for user caching
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

# CORS Setup
def setup_cors(app):
    """ 
    Configures Cross-Origin Resource Sharing (CORS) for the FastAPI application.

    This function adds middleware to the app to allow requests from any origin, enabling 
    cross-origin communication with the API.

    Args:
        app (FastAPI): The FastAPI application instance to configure.

    Returns:
        None
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# User Registration with Email Verification
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """ 
    Registers a new user with email verification.

    Creates a new user in the database and sends an email verification link. The 
    user is marked as unverified initially.

    Args:
        user (UserCreate): The user data for registration.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the user already exists in the database.

    Returns:
        dict: Contains the user ID, email, and a message for email verification.
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    
    new_user = User(email=user.email, hashed_password=hash_password(user.password), is_verified=False)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Email verification (stub)
    verification_link = f"http://localhost:8000/verify-email?email={user.email}"
    print(f"Please verify your email: {verification_link}")

    return {"id": new_user.id, "email": new_user.email, "message": "Please verify your email"}

@router.get("/verify-email")
def verify_email(email: str, db: Session = Depends(get_db)):
    """ 
    Verifies the user's email address.

    Updates the user's verification status in the database after they click the 
    verification link sent to their email.

    Args:
        email (str): The email address of the user to verify.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the user is not found in the database.

    Returns:
        dict: A success message indicating the email was verified.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    db.commit()
    return {"message": "Email successfully verified"}

# User Login and Token Generation
@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """ 
    Logs in a user and generates access and refresh tokens.

    Validates the user's credentials and generates access and refresh tokens for authentication.

    Args:
        user (UserLogin): The user credentials for login.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the credentials are invalid.

    Returns:
        dict: Contains the access and refresh tokens.
    """
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": db_user.email})
    refresh_token = create_refresh_token({"sub": db_user.email})

    db_user.refresh_token = refresh_token
    db.commit()

    # Caching the user in Redis
    redis_client.set(f"user:{db_user.email}", db_user.email, ex=3600)

    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """ 
    Refreshes the access token using a valid refresh token.

    Verifies the provided refresh token and generates a new access token.

    Args:
        refresh_token (str): The refresh token to use for generating a new access token.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the refresh token is invalid.

    Returns:
        dict: Contains the new access and refresh tokens.
    """
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    db_user = db.query(User).filter(User.email == payload["sub"]).first()
    if not db_user or db_user.refresh_token != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_access_token = create_access_token({"sub": db_user.email})
    return {"access_token": new_access_token, "refresh_token": refresh_token}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """ 
    Retrieves the current user from the provided OAuth2 token.

    Decodes the token, verifies it, and retrieves the user from the database.

    Args:
        token (str): The OAuth2 access token to authenticate the user.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the token is invalid or the user does not exist.

    Returns:
        User: The current authenticated user.
    """
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# CRUD operations for contacts with rate limiting
@router.post("/contacts/", response_model=ContactResponse, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def create_contact(contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Creates a new contact for the authenticated user.

    Adds a new contact record to the database for the current authenticated user.

    Args:
        contact (ContactCreate): The contact data to create.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        ContactResponse: The created contact data.
    """
    new_contact = Contact(**contact.dict(), user_id=current_user.id)
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

@router.get("/contacts/", response_model=list[ContactResponse])
def get_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Retrieves all contacts for the authenticated user.

    Args:
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        list[ContactResponse]: A list of contacts associated with the current user.
    """
    return db.query(Contact).filter(Contact.user_id == current_user.id).all()

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Retrieves a specific contact by ID for the authenticated user.

    Args:
        contact_id (int): The ID of the contact to retrieve.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: If the contact is not found.

    Returns:
        ContactResponse: The contact data.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, updated_contact: ContactCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Updates an existing contact for the authenticated user.

    Args:
        contact_id (int): The ID of the contact to update.
        updated_contact (ContactCreate): The new contact data.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: If the contact is not found.

    Returns:
        ContactResponse: The updated contact data.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in updated_contact.dict().items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact

@router.delete("/contacts/{contact_id}", response_model=dict)
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Deletes a contact by ID for the authenticated user.

    Args:
        contact_id (int): The ID of the contact to delete.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Raises:
        HTTPException: If the contact is not found.

    Returns:
        dict: A message indicating the contact was deleted.
    """
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == current_user.id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}

@router.get("/contacts/search/", response_model=list[ContactResponse])
def search_contacts(query: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Searches for contacts by name or email for the authenticated user.

    Args:
        query (str): The search query.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        list[ContactResponse]: A list of contacts that match the query.
    """
    contacts = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        (Contact.first_name.ilike(f"%{query}%")) |
        (Contact.last_name.ilike(f"%{query}%")) |
        (Contact.email.ilike(f"%{query}%"))
    ).all()
    return contacts

@router.get("/contacts/birthdays/", response_model=list[ContactResponse])
def get_upcoming_birthdays(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ 
    Retrieves contacts with upcoming birthdays in the next week.

    Args:
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).

    Returns:
        list[ContactResponse]: A list of contacts with birthdays in the next 7 days.
    """
    today = datetime.today().date()
    next_week = today + timedelta(days=7)
    contacts = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.birthday.between(today, next_week)
    ).all()
    return contacts

@router.post("/upload-avatar")
def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """ 
    Uploads a new avatar for the current user.

    Args:
        file (UploadFile): The avatar image file to upload.
        current_user (User, optional): The authenticated user. Defaults to Depends(get_current_user).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        dict: The URL of the uploaded avatar.
    """
    upload_result = cloudinary.uploader.upload(file.file, folder="avatars")
    current_user.avatar_url = upload_result["secure_url"]
    db.commit()
    return {"avatar_url": current_user.avatar_url}
