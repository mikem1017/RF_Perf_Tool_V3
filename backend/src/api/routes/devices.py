"""
Device management routes.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from backend.src.core.schemas.device import Device, DeviceConfig
from backend.src.storage.interfaces import IDatabase
from backend.src.api.dependencies import get_database


router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.post("", response_model=dict, status_code=201)
def create_device(device: DeviceConfig, db: IDatabase = Depends(get_database)):
    """Create a new device."""
    try:
        device_id = db.create_device({
            "name": device.name,
            "part_number": device.part_number,
            "description": device.description,
            "s_parameter_config": device.s_parameter_config.model_dump() if device.s_parameter_config else None,
        })
        return {"id": device_id, "message": "Device created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[dict])
def list_devices(db: IDatabase = Depends(get_database)):
    """List all devices."""
    # Note: This requires adding a list method to IDatabase interface
    # For now, return empty list
    return []


@router.get("/{device_id}", response_model=dict)
def get_device(device_id: int, db: IDatabase = Depends(get_database)):
    """Get a device by ID."""
    device = db.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=dict)
def update_device(device_id: int, device: DeviceConfig, db: IDatabase = Depends(get_database)):
    """Update a device."""
    # Note: This requires adding an update method to IDatabase interface
    raise HTTPException(status_code=501, detail="Update not yet implemented")


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, db: IDatabase = Depends(get_database)):
    """Delete a device."""
    # Note: This requires adding a delete method to IDatabase interface
    raise HTTPException(status_code=501, detail="Delete not yet implemented")

