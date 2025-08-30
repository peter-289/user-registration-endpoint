from sqlalchemy import Column, String, Boolean, Integer, Enum, DateTime
from database.database_setup import Base
import enum
from datetime import datetime

class UserRole(enum.Enum):
    USER="user"
    ANONYMOUS_USER="anonymous_user"
    ADMIN="admin"

class User(Base):
    __tablename__="users"

    id=Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name=Column(String,nullable=False)
    user_name=Column(String, unique=True, nullable=False)
    email=Column(String, unique=True, nullable=False)
    password=Column(String(255),unique=True,nullable=False)
    role=Column(Enum(UserRole), default=UserRole.ANONYMOUS_USER,nullable=False)
    is_active=Column(Boolean, default=True)
    time_registered=Column(DateTime, default=datetime.utcnow)