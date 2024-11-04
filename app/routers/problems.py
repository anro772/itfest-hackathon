# app/routers/problems.py
from fastapi import APIRouter, HTTPException, Depends
from app.services.firebase_service import FirebaseService
from app.models.problem import ProblemCreate, Problem, ProblemCategory
from app.dependecies.auth import get_current_user
from app.models.user import User
from typing import List
from pydantic import BaseModel

router = APIRouter()
firebase_service = FirebaseService()

@router.post("/", response_model=Problem)
async def create_problem(
    problem: ProblemCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        # Use the current_user's ID for problem creation
        return await firebase_service.create_problem(problem, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Add an endpoint to get available problem categories
@router.get("/categories", response_model=List[ProblemCategory])
async def get_problem_categories():
    return await firebase_service.get_problem_categories()

@router.get("/area", response_model=List[Problem])
async def get_problems_in_area(min_lat: float, max_lat: float, 
                             min_lng: float, max_lng: float):
    return await firebase_service.get_problems_in_area(
        min_lat, max_lat, min_lng, max_lng)
class InteractionRequest(BaseModel):
    interaction_type: str

@router.post("/{problem_id}/interact")
async def interact_with_problem(
    problem_id: str,
    interaction: InteractionRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        return await firebase_service.interact_with_problem(
            problem_id=problem_id,
            user_id=current_user.id,
            interaction_type=interaction.interaction_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))