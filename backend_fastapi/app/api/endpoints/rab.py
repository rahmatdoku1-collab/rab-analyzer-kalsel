from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.post("/generate", summary="Auto RAB Generator")
def generate_auto_rab(prompt: str, db: Session = Depends(get_db)):
    """
    Integrates with OpenRouter AI to generate a full RAB from a single sentence prompt.
    Will connect to the services/ai_generator.py logic in the future.
    """
    # Mocking for Phase 6.3 endpoint structure
    return {
        "status": "success",
        "message": "AI is processing your request",
        "mock_result": {
            "project_name": "Generated Project from: " + prompt,
            "total_estimated_budget": 150000000
        }
    }
