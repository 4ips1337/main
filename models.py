from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    """ 
    Represents a user in the system.

    This class maps to the 'users' table in the database and defines the properties 
    associated with a user, such as email, hashed password, and refresh token. 
    It also establishes a relationship to the `Contact` model.

    Attributes:
        id (int): The unique identifier for the user.
        email (str): The email address of the user.
        hashed_password (str): The hashed password of the user.
        refresh_token (str, optional): The refresh token for the user (nullable).
        contacts (list): A list of contacts associated with the user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)  # For storing refresh token

    contacts = relationship("Contact", back_populates="owner")

class Contact(Base):
    """ 
    Represents a contact in the system.

    This class maps to the 'contacts' table in the database and defines the 
    properties associated with a contact, such as name and phone number. 
    It also establishes a relationship to the `User` model via the `owner` field.

    Attributes:
        id (int): The unique identifier for the contact.
        name (str): The name of the contact.
        phone (str): The phone number of the contact.
        owner_id (int): The identifier of the user who owns the contact.
        owner (User): The user associated with this contact.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="contacts")
