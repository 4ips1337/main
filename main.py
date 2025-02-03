from fastapi import FastAPI
from models import Base
from database import engine
from routes import router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(router)
