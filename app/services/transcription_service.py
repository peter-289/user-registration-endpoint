# backend/app/services/transcription_service.py
import os
from sqlalchemy.orm import Session
from app.models.transcription_model import Transcription
from app.models.model_loader import get_model
from fastapi import HTTPException, status
from app.constants.paths import DOWNLOAD_DIR
from os.path import splitext

def transcribe_audio(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File does not exist!")
    
    model = get_model()
    try:
      result = model.transcribe(file_path)
      return result["text"]
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Transcription failed {str(e)}")


def process_and_store_transcription(file_path: str, db: Session) -> Transcription:

    try:
     filename = os.path.basename(file_path)
     transcript_text = transcribe_audio(file_path)
     
     txt_filename = splitext(filename)[0] + ".txt"
     txt_file_path = DOWNLOAD_DIR / txt_filename
     with open(txt_file_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

     record = Transcription(
        filename=filename,
        transcript=transcript_text
     )

     db.add(record)
     db.commit()
     db.refresh(record)

     return record
    except HTTPException:
       raise
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")