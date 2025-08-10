from pydantic import BaseModel
from datetime import datetime


class TranscriptionIn(BaseModel):
    filename:str
    transcript:str
    

class TranscriptionOut(BaseModel):
    id:int
    filename:str
    transcript:str
    uploaded_at:datetime

    class Config:
        from_attributes=True