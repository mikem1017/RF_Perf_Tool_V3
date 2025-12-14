"""
Test run management routes.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pathlib import Path
from backend.src.core.schemas.test_run import TestRun, TestRunStatus
from backend.src.storage.interfaces import IDatabase, IFileStorage
from backend.src.api.dependencies import get_database, get_file_storage, get_test_run_service
from backend.src.services.test_run_service import TestRunService
from backend.src.core.schemas.device import DeviceConfig
from backend.src.core.schemas.requirement_set import RequirementSet


router = APIRouter(prefix="/api/test-runs", tags=["test-runs"])


@router.post("", response_model=dict, status_code=201)
def create_test_run(
    test_run: TestRun,
    db: IDatabase = Depends(get_database),
):
    """Create a new test run."""
    try:
        test_run_id = db.create_test_run({
            "device_id": test_run.device_id,
            "test_stage_id": test_run.test_stage_id,
            "requirement_set_id": test_run.requirement_set_id,
            "test_type": test_run.test_type,
        })
        return {"id": test_run_id, "message": "Test run created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[dict])
def list_test_runs(db: IDatabase = Depends(get_database)):
    """List all test runs."""
    # Note: This requires adding a list method to IDatabase interface
    return []


@router.get("/{test_run_id}", response_model=dict)
def get_test_run(test_run_id: int, db: IDatabase = Depends(get_database)):
    """Get a test run by ID."""
    test_run = db.get_test_run(test_run_id)
    if test_run is None:
        raise HTTPException(status_code=404, detail="Test run not found")
    return test_run


@router.post("/{test_run_id}/upload", response_model=dict, status_code=200)
async def upload_files(
    test_run_id: int,
    files: List[UploadFile] = File(...),
    db: IDatabase = Depends(get_database),
    file_storage: IFileStorage = Depends(get_file_storage),
):
    """
    Upload S-parameter files for a test run.
    
    Note: This endpoint only stores files. Processing requires device_config and requirement_set.
    """
    
    # Verify test run exists
    test_run = db.get_test_run(test_run_id)
    if test_run is None:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    uploaded_files = []
    for file in files:
        content = await file.read()
        stored_path = file_storage.store_uploaded_file(test_run_id, file.filename, content)
        uploaded_files.append({"filename": file.filename, "stored_path": str(stored_path)})
    
    return {
        "test_run_id": test_run_id,
        "uploaded_files": uploaded_files,
        "message": f"Uploaded {len(uploaded_files)} file(s)",
    }


@router.post("/{test_run_id}/process", response_model=dict, status_code=200)
async def process_test_run(
    test_run_id: int,
    device_config: DeviceConfig,
    requirement_set: RequirementSet,
    service: TestRunService = Depends(get_test_run_service),
):
    """
    Process a test run: parse, load, compute, evaluate.
    
    Requires device_config and requirement_set to be provided.
    Files must already be uploaded via /upload endpoint.
    """
    try:
        # Get file paths from database
        # TODO: Implement file retrieval from database
        # For now, this is a placeholder
        raise HTTPException(status_code=501, detail="Processing not yet fully implemented")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_run_id}/compliance", response_model=dict)
def get_compliance(test_run_id: int, db: IDatabase = Depends(get_database)):
    """Get compliance results for a test run."""
    test_run = db.get_test_run(test_run_id)
    if test_run is None:
        raise HTTPException(status_code=404, detail="Test run not found")
    
    # TODO: Retrieve compliance results from database
    return {"test_run_id": test_run_id, "compliance": "Not yet implemented"}

