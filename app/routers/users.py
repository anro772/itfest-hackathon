from fastapi import APIRouter, HTTPException, Depends
from app.services.firebase_service import FirebaseService
from app.models.user import UserCreate, UserLogin, User
from fastapi.responses import JSONResponse
from typing import List
import asyncio
from app.auth.jwt_handler import create_access_token, verify_token

router = APIRouter()
firebase_service = FirebaseService()

@router.post("/register")
async def create_user(user: UserCreate):
    try:
        return await firebase_service.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/login")
async def login_user(login: UserLogin):
    try:
        user = await firebase_service.login_user(login)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "username": user.username
        }
        access_token = create_access_token(token_data)
        
        # Convert user model to dictionary for response
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "credibility_score": user.credibility_score,
            "rank": user.rank,
            "created_problems": user.created_problems,
            "access_token": access_token
        }
        return JSONResponse(content=user_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}/credibility")
async def get_credibility(user_id: str):
    try:
        score = await firebase_service.get_user_credibility(user_id)
        return {"credibility_score": score}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.get("/all", response_model=List[User])
async def get_all_users():
    try:
        users = await asyncio.to_thread(firebase_service.get_all_users)
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        return users
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    try:
        user = await firebase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))