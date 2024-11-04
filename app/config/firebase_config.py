import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import os

def initialize_firebase():
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Get the absolute path to credentials file
        cred_path = Path(__file__).parent.parent.parent / "firebase-credentials.json"
        
        if not cred_path.exists():
            raise FileNotFoundError("Firebase credentials file not found!")
        
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

