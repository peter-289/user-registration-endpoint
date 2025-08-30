from pydantic import BaseModel, EmailStr
from models.user_model import UserRole

class UserCreate(BaseModel):
    full_name:str
    user_name:str
    email:EmailStr
    password:str

    class Config:
        from_attributes=True

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    role:UserRole
    is_active:bool
    #time_registered:datetime

    class Config:
        from_attributes=True

