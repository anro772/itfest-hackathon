from fastapi import Depends, HTTPException
from app.auth.jwt_handler import verify_token
from app.services.firebase_service import FirebaseService
from app.models.user import User

firebase_service = FirebaseService()

async def get_current_user(token: dict = Depends(verify_token)) -> User:
    try:
        user_id = token.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        user = await firebase_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))