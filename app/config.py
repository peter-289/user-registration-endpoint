from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WHISPER_MODEL_SIZE: str = "tiny"  # Options: tiny, base, small, medium, large
    MY_API_KEY: str
    DATABASE_URL:str
    ADMIN_PASSWORD:str
    FRONTEND_URL: str = "http://localhost:3000"  # Default to localhost for development

    class Config:
        env_file = ".env"

settings = Settings()
