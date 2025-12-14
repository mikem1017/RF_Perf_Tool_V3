"""
Test stage management routes.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from backend.src.core.schemas.test_stage import TestStage
from backend.src.storage.interfaces import IDatabase
from backend.src.api.dependencies import get_database


router = APIRouter(prefix="/api/test-stages", tags=["test-stages"])


@router.post("", response_model=dict, status_code=201)
def create_test_stage(stage: TestStage, db: IDatabase = Depends(get_database)):
    """Create a new test stage."""
    try:
        stage_id = db.create_test_stage({
            "name": stage.name,
            "description": stage.description,
        })
        return {"id": stage_id, "message": "Test stage created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[dict])
def list_test_stages(db: IDatabase = Depends(get_database)):
    """List all test stages."""
    # Note: This requires adding a list method to IDatabase interface
    return []


@router.get("/{stage_id}", response_model=dict)
def get_test_stage(stage_id: int, db: IDatabase = Depends(get_database)):
    """Get a test stage by ID."""
    stage = db.get_test_stage(stage_id)
    if stage is None:
        raise HTTPException(status_code=404, detail="Test stage not found")
    return stage

