# backend/app/routes/transcription_routes.py

import shutil
from pathlib import Path
import uuid
from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.schemas.transcription_schema import TranscriptionOut
from app.services.transcription_service import process_and_store_transcription
from app.models.database import SessionLocal
from app.constants.paths import UPLOAD_DIR, DOWNLOAD_DIR
from fastapi.responses import FileResponse
from app.models.transcription_model import Transcription
from datetime import datetime, timedelta
from app.security.admin_ import admin_auth

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/transcribe", response_model=TranscriptionOut)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".mp3", ".wav", ".m4a", ".mp4", ".webm")):
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        
        
        record = process_and_store_transcription(str(file_path), db)
        

        return record
    
    except HTTPException as e:
        raise e
   
    finally:
        file.file.close()
        if file_path.exists():
            file_path.unlink(missing_ok=True)

#-----Download Link------
@router.get("/transcription/download/{filename}")
def download_transcription(filename: str):
    file_name_no_ext = Path(filename).stem
    txt_file_path = DOWNLOAD_DIR / f"{file_name_no_ext}.txt"

    if not txt_file_path.exists():
        raise HTTPException(status_code=404, detail="Transcript file not found.")

    return FileResponse(
        path=txt_file_path,
        media_type="text/plain",
        filename=filename
    )


DOWNLOAD_DIR = DOWNLOAD_DIR


##-----Download Link------
@router.get("/transcription/download-link/{filename}")
def get_transcription_url(filename: str, request: Request):
    txt_file_path = DOWNLOAD_DIR / filename
    ##txt_filename = Path(filename).stem + ".txt"

    if not txt_file_path.exists():
        raise HTTPException(status_code=404, detail="Transcript file not found.")

    # Absolute URL
    download_url = str(request.base_url) + f"transcription/download/{filename}"

    return {"download_url": download_url}



#####---Get All Transcriptions----
@router.get("/transcriptions/all",response_model=list[TranscriptionOut])
def get_all_transcriptions(db:Session=Depends(get_db)):
    try:
     transcriptions=db.query(Transcription).all()
    except:
        raise HTTPException(status_code=404, detail="No transcriptions found!")
    return transcriptions



##------Admin Only------
@router.delete("/transcriptions/delete", status_code=204,dependencies=[Depends(admin_auth)])
def delete_old_transcripts(
    db:Session=Depends(get_db),
    minutes:int=Query(60, description="Delete transcripts older than time: x")
                           ):
    Threshold=datetime.utcnow() - timedelta(minutes=minutes)
    deleted=db.query(Transcription).filter(Transcription.uploaded_at < Threshold).delete()
    db.commit()
    return{
        "message":f"{deleted} old transcripts deleted!"
    }

