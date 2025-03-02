from fastapi import FastAPI
from models import Base
from database import engine
from routes import router

app = FastAPI()


Base.metadata.create_all(bind=engine)


app.include_router(router)

def create_app():
    """ 
    Create and configure the FastAPI application.

    This function sets up the database tables if they do not exist and includes the
    necessary router for handling requests.

    Returns:
        FastAPI: The FastAPI application instance.

    Example:
        app = create_app()
        app.run()
    """
    return app
