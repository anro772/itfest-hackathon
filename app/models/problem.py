from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ProblemCategory(BaseModel):
    id: str
    name: str
    description: str
    color: str

class ProblemCreate(BaseModel):
    category_id: str
    description: str
    latitude: float
    longitude: float

class Problem(BaseModel):
    id: str
    category_id: str
    description: str
    latitude: float
    longitude: float
    created_by: str
    created_at: datetime
    category_description: Optional[str] = Field(default="Unknown Category")
    color: Optional[str] = Field(default="red")
    likes: int = 0
    dislikes: int = 0
    no_longer_exists_count: int = 0
    is_active: bool = True
    liked_by: List[str] = []
    disliked_by: List[str] = []
    reported_nonexistent_by: List[str] = []

