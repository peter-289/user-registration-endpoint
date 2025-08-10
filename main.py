# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from  app.models.database import Base, engine
from app.models import transcription_model
from app.routes import transcription_routes
import os

app = FastAPI()

origins = [os.getenv("FRONTEND_URL"),  # Default to localhost for development
           ]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

#routes
app.include_router(transcription_routes.router,  prefix="/api", tags=["Transcription"])

@app.get("/")
def root():
    return {"message": " Nothing much for you here. Welcome to Tech Pulse Transcription API"}
