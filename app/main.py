from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config.firebase_config import initialize_firebase
from app.routers import problems, users
import os

app = FastAPI(title="Bucharest Problems API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase at startup
@app.on_event("startup")
async def startup_event():
    initialize_firebase()

# Include API routers BEFORE mounting static files
app.include_router(problems.router, prefix="/api/problems", tags=["problems"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

# Mount static files AFTER including routers
app.mount("/", StaticFiles(directory="client", html=True), name="client")

# Optional: Fallback route for SPA-like behavior
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if os.path.exists(f"client/{full_path}"):
        return FileResponse(f"client/{full_path}")
    return FileResponse("client/index.html")