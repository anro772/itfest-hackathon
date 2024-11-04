from app.config.firebase_config import initialize_firebase
# app/services/firebase_service.py
from firebase_admin import firestore
from typing import Optional, List, Dict
from app.models.user import User, UserCreate, UserLogin
from app.models.problem import Problem, ProblemCreate, ProblemCategory
from datetime import datetime
import bcrypt
from typing import List
import asyncio


class FirebaseService:
    def __init__(self):
        self.db = initialize_firebase()
        self.MIN_CREDIBILITY = 0
        self.MAX_CREDIBILITY = 2000
        self.LIKE_SCORE_BONUS = 10
        self.NEGATIVE_RATIO_PENALTY = 50

    def get_all_users(self) -> List[User]:
        try:
            users_ref = self.db.collection('users').get()  # Retrieve all users
            users = [
                User(id=user.id, **user.to_dict()) for user in users_ref
            ]
            return users
        except Exception as e:
            print(f"Error fetching all users: {str(e)}")
            raise ValueError("Error fetching all users")
        
    async def get_user_credibility(self, user_id: str) -> int:
        try:
            # Fetch the user's document
            user_doc = self.db.collection('users').document(user_id).get()
            
            # Check if the user exists
            if not user_doc.exists:
                raise ValueError("User not found")
            
            # Retrieve and return the credibility score
            user_data = user_doc.to_dict()
            credibility_score = user_data.get("credibility_score", self.MIN_CREDIBILITY)
            return credibility_score
        except Exception as e:
            print(f"Error fetching user credibility: {str(e)}")
            raise ValueError("Error fetching user credibility")

        
    async def create_user(self, user: UserCreate) -> User:
        # Check if user exists
        existing_users = self.db.collection('users').where('email', '==', user.email).get()
        if len(list(existing_users)) > 0:
            raise ValueError("User already exists")
            
        # Hash password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt)
        
        user_data = {
            "username": user.username,
            "email": user.email,
            "password": hashed_password.decode('utf-8'),
            "credibility_score": 1000,
            "rank": "Beginner",
            "created_problems": [],
            "created_at": datetime.now()
        }
        
        doc_ref = self.db.collection('users').document()
        doc_ref.set(user_data)
        
        return User(id=doc_ref.id, **user_data)

    async def login_user(self, login: UserLogin) -> Optional[User]:
        users = self.db.collection('users').where('email', '==', login.email).get()
        
        for user in users:
            user_data = user.to_dict()
            if bcrypt.checkpw(login.password.encode('utf-8'), 
                            user_data['password'].encode('utf-8')):
                return User(id=user.id, **user_data)
            

    async def get_problem_categories(self) -> List[ProblemCategory]:
        """Fetch all problem categories and return them as a list"""
        try:
            categories = self.db.collection('problem_categories').get()
            # Convert the categories directly to a list
            return [
                ProblemCategory(
                    id=cat.id,
                    name=cat.to_dict()['name'],
                    description=cat.to_dict()['description'],
                    color=cat.to_dict()['color']
                )
                for cat in categories
            ]
        except Exception as e:
            print(f"Error fetching categories: {str(e)}")
            return []
    async def get_problems_in_area(self, min_lat: float, max_lat: float, 
                                 min_lng: float, max_lng: float) -> List[Problem]:
        try:
            # First get all categories
            categories = self.db.collection('problem_categories').get()
            categories = {
                cat.id: ProblemCategory(id=cat.id, **cat.to_dict())
                for cat in categories
            }
            # Query problems
            problems_ref = self.db.collection('problems')\
                .where('is_active', '==', True)\
                .order_by('latitude')\
                .start_at({'latitude': min_lat})\
                .end_at({'latitude': max_lat})
            
            problems = problems_ref.get()
            
            result = []
            for prob in problems:
                prob_data = prob.to_dict()
                if min_lng <= prob_data.get('longitude', 0) <= max_lng:
                    # Add category description to problem data
                    category = categories.get(prob_data.get('category_id', ''))
                    prob_data['category_description'] = category.description if category else 'Unknown Category'
                    prob_data['color'] = category.color if category else 'red'
                    print(prob_data)
                    result.append(Problem(id=prob.id, **prob_data))
            
            return result
            
        except Exception as e:
            print(f"Error fetching problems: {str(e)}")
            raise ValueError(f"Error fetching problems: {str(e)}")

    async def get_user(self, user_id: str) -> Optional[User]:
        try:
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                return None
            user_data = user_doc.to_dict()
            return User(id=user_doc.id, **user_data)
        except Exception as e:
            print(f"Error fetching user: {str(e)}")
            raise ValueError("Error fetching user")
    
    async def create_problem(self, problem: ProblemCreate, user_id: str) -> Problem:
        # Validate category exists
        category_ref = self.db.collection('problem_categories').document(problem.category_id)
        category = category_ref.get()
        if not category.exists:
            raise ValueError("Invalid problem category")

        # Validate user exists
        user_ref = self.db.collection('users').document(user_id)
        user = user_ref.get()
        if not user.exists:
            raise ValueError("Invalid user")

        problem_data = {
            **problem.dict(),
            "created_by": user_id,
            "created_at": datetime.now(),
            "likes": 0,
            "dislikes": 0,
            "no_longer_exists_count": 0,
            "is_active": True,
            "liked_by": [],
            "disliked_by": [],
            "reported_nonexistent_by": []
        }
        
        doc_ref = self.db.collection('problems').document()
        doc_ref.set(problem_data)
        
        # Add to user's created problems
        user_ref.update({
            "created_problems": firestore.ArrayUnion([doc_ref.id])
        })
        
        return Problem(id=doc_ref.id, **problem_data)

    async def _update_creator_score(self, user_id: str, score_change: int):
        """Update a user's credibility score"""
        try:
            # Get user reference
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return
                
            user_data = user_doc.to_dict()
            current_score = user_data.get('credibility_score', 1000)
            
            # Calculate new score within bounds
            new_score = max(
                min(current_score + score_change, self.MAX_CREDIBILITY),
                self.MIN_CREDIBILITY
            )
            
            # Update user's credibility score
            user_ref.update({
                "credibility_score": new_score
            })
            
            # Update rank based on new score
            new_rank = self._calculate_rank(new_score)
            if new_rank != user_data.get('rank'):
                user_ref.update({
                    "rank": new_rank
                })
                
        except Exception as e:
            print(f"Error updating creator score: {str(e)}")
            raise ValueError(f"Error updating creator score: {str(e)}")

    def _calculate_rank(self, score: int) -> str:
        """Calculate user rank based on credibility score"""
        if score < 500:
            return "Bronze"
        elif score < 1000:
            return "Silver"
        elif score < 1500:
            return "Gold"
        elif score < 2000:
            return "Diamond"
        else:
            return "Diamond"

    async def interact_with_problem(self, problem_id: str, user_id: str, 
                                  interaction_type: str) -> Problem:
        problem_ref = self.db.collection('problems').document(problem_id)
        problem = problem_ref.get()
        
        if not problem.exists:
            raise ValueError("Problem not found")
            
        problem_data = problem.to_dict()
        
        # Check if user is the creator
        if problem_data['created_by'] == user_id:
            raise ValueError("Cannot interact with own problem")
            
        # Handle different interaction types
        updates = {}
        if interaction_type == "like":
            if user_id in problem_data['disliked_by']:
                updates['dislikes'] = firestore.Increment(-1)
                updates['disliked_by'] = firestore.ArrayRemove([user_id])
            if user_id not in problem_data['liked_by']:
                updates['likes'] = firestore.Increment(1)
                updates['liked_by'] = firestore.ArrayUnion([user_id])
                # Update creator's credibility score
                await self._update_creator_score(problem_data['created_by'], 
                                              self.LIKE_SCORE_BONUS)
                
        elif interaction_type == "dislike":
            if user_id in problem_data['liked_by']:
                updates['likes'] = firestore.Increment(-1)
                updates['liked_by'] = firestore.ArrayRemove([user_id])
            if user_id not in problem_data['disliked_by']:
                updates['dislikes'] = firestore.Increment(1)
                updates['disliked_by'] = firestore.ArrayUnion([user_id])
                
        elif interaction_type == "no_longer_exists":
            if user_id not in problem_data['reported_nonexistent_by']:
                updates['no_longer_exists_count'] = firestore.Increment(1)
                updates['reported_nonexistent_by'] = firestore.ArrayUnion([user_id])
                
        if updates:
            problem_ref.update(updates)
            
            # Check conditions for deactivating problem
            updated_problem = problem_ref.get().to_dict()
            if (updated_problem['likes'] - updated_problem['dislikes'] <= -2 or 
                updated_problem['no_longer_exists_count'] >= 3):
                problem_ref.update({"is_active": False})
                # Apply penalty to creator's credibility score only if dislike ratio is bad
                if updated_problem['likes'] - updated_problem['dislikes'] <= -2:
                    await self._update_creator_score(problem_data['created_by'], 
                                                  -self.NEGATIVE_RATIO_PENALTY)
                                                  
            # Get the updated problem data for return
            final_problem = problem_ref.get()
            return Problem(id=final_problem.id, **final_problem.to_dict())
        
        return Problem(id=problem.id, **problem_data)
