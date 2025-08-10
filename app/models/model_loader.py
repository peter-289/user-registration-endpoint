# backend/app/models/model_loader.py

import whisper
from functools import lru_cache
from app.config import settings

@lru_cache()
def get_model():
    return whisper.load_model(settings.WHISPER_MODEL_SIZE)
