# app/models/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: str
    credibility_score: int = 1000
    rank: str = "Beginner"
    created_problems: List[str] = []  # List of problem IDs
    
    class Config:
        from_attributes = True