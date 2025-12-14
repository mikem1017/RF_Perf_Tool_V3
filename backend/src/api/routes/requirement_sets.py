"""
Requirement set management routes.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from backend.src.core.schemas.requirement_set import RequirementSet
from backend.src.storage.interfaces import IDatabase
from backend.src.api.dependencies import get_database


router = APIRouter(prefix="/api/requirement-sets", tags=["requirement-sets"])


@router.post("", response_model=dict, status_code=201)
def create_requirement_set(req_set: RequirementSet, db: IDatabase = Depends(get_database)):
    """Create a new requirement set."""
    try:
        req_set_id = db.create_requirement_set({
            "name": req_set.name,
            "test_type": req_set.test_type,
            "metric_limits": [limit.model_dump() for limit in req_set.metric_limits],
            "pass_policy": req_set.pass_policy.model_dump() if req_set.pass_policy else None,
            "requirement_hash": req_set.compute_hash(),
        })
        return {"id": req_set_id, "message": "Requirement set created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[dict])
def list_requirement_sets(db: IDatabase = Depends(get_database)):
    """List all requirement sets."""
    # Note: This requires adding a list method to IDatabase interface
    return []


@router.get("/{req_set_id}", response_model=dict)
def get_requirement_set(req_set_id: int, db: IDatabase = Depends(get_database)):
    """Get a requirement set by ID."""
    req_set = db.get_requirement_set(req_set_id)
    if req_set is None:
        raise HTTPException(status_code=404, detail="Requirement set not found")
    return req_set

