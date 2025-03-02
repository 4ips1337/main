from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

def get_db():
    """ 
    Creates and yields a session object for interacting with the database.

    This function uses a context manager to ensure that the session is properly closed
    after database operations are complete.

    Yields:
        Session: A session object for database operations.

    Example:
        with get_db() as db:
            result = db.query(MyModel).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()