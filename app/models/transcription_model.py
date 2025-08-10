from sqlalchemy import Column, String,Integer, DateTime
from datetime import datetime
from app.models.database import Base

class Transcription(Base):
    __tablename__ ="transcription"

    id =Column(Integer,index=True,autoincrement=True, primary_key=True)
    filename =Column(String)
    transcript =Column(String)
    uploaded_at=Column(DateTime, default=datetime.utcnow)