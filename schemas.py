from pydantic import BaseModel, EmailStr, Field
from datetime import date


class ContactCreate(BaseModel):
    """ 
    Contact data model for creating a new contact.

    This model is used when creating a new contact. It includes basic contact information such as name, email, phone number,
    birthday, and additional information.

    Attributes:
        first_name (str): The first name of the contact, with a maximum length of 50 characters.
        last_name (str): The last name of the contact, with a maximum length of 50 characters.
        email (EmailStr): The email address of the contact.
        phone_number (str): The phone number of the contact.
        birthday (date): The birthday of the contact.
        additional_info (str | None): Additional information about the contact. It is optional.
    """
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: str | None = None


class ContactResponse(ContactCreate):
    """ 
    Response model for a contact, including the ID.

    This model is used when returning contact information, adding the ID of the contact to the data.
    It inherits from the `ContactCreate` model, with the addition of the `id` field.

    Attributes:
        id (int): The unique identifier of the contact.
    """
    id: int

    class Config:
        """ Configuration for serialization of attributes """
        from_attributes = True


class UserCreate(BaseModel):
    """ 
    User data model for creating a new user.

    This model is used when creating a new user. It includes the username, email, and password of the user.

    Attributes:
        username (str): The username of the user, with a maximum length of 100 characters.
        email (EmailStr): The email address of the user.
        password (str): The password of the user, with a minimum length of 6 characters.
    """
    username: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """ 
    User data model for logging in a user.

    This model is used when the user provides credentials to log in. It includes the email and password of the user.

    Attributes:
        email (EmailStr): The email address of the user.
        password (str): The password of the user.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """ 
    Response model for a token after user authentication.

    This model is used when returning an access token and token type after a successful login.

    Attributes:
        access_token (str): The access token generated after successful authentication.
        token_type (str): The type of token (e.g., "bearer").
    """
    access_token: str
    token_type: str
    