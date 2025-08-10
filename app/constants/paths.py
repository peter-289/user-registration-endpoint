# backend/app/constants/paths.py

from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parent.parent /"uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

DOWNLOAD_DIR=Path(__file__).resolve().parent.parent /"downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)