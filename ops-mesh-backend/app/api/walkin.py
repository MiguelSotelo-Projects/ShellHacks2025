"""
Walk-in API routes - Member 2 responsibility
Handles walk-in patient intake using Google ADK agents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Optional
import redis
from databases import Database
import uuid
from datetime import datetime

from app.api.deps import get_database, get_redis
from app.services.walkin_service import WalkInService

router = APIRouter()

# Initialize service
walkin_service = WalkInService()


# Request/Response Models
class WalkInRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    reason: str
    urgency: int  # 1-5 scale, 5 being most urgent
    preferred_department: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()

    @validator('urgency')
    def validate_urgency(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Urgency must be between 1 and 5')
        return v

    @validator('reason')
    def validate_reason(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Reason must be at least 5 characters')
        return v.strip()


class WalkInResponse(BaseModel):
    success: bool
    patient_id: Optional[str] = None
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None  # minutes
    check_in_time: Optional[str] = None
    error_message: Optional[str] = None


class PatientStatusResponse(BaseModel):
    patient_id: str
    status: str
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None
    check_in_time: Optional[str] = None
    urgency: int
    last_updated: str


@router.post("/walkin", response_model=WalkInResponse)
async def submit_walkin(
        request: WalkInRequest,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """
    Submit walk-in patient intake using Google ADK agent.

    Processes patient data through intake agent and adds to queue system.
    """

    try:
        # Use service layer for processing
        result = await walkin_service.process_walkin_intake(request)

        if not result["success"]:
            return WalkInResponse(
                success=False,
                error_message=result["error_message"]
            )

        patient_data = result["patient_data"]

        # Add to Redis queue - coordinating with Member 3's queue system
        patient_id = patient_data["patient_id"]

        # Calculate queue position
        current_queue_size = redis_client.llen("walkin_queue") or 0
        queue_position = current_queue_size + 1

        # Calculate estimated wait time based on urgency and queue
        base_wait_time = queue_position * 15  # 15 min base per position
        urgency_multiplier = {5: 0.5, 4: 0.7, 3: 1.0, 2: 1.2, 1: 1.5}
        estimated_wait_time = int(base_wait_time * urgency_multiplier.get(request.urgency, 1.0))

        # Store patient data in Redis
        redis_patient_data = {
            "patient_id": patient_id,
            "name": request.name,
            "phone": request.phone or "",
            "reason": request.reason,
            "urgency": request.urgency,
            "preferred_department": request.preferred_department or "",
            "check_in_time": datetime.now().isoformat(),
            "status": "waiting",
            "queue_position": queue_position,
            "estimated_wait_time": estimated_wait_time
        }

        # Add to queue and store patient data
        redis_client.lpush("walkin_queue", patient_id)
        redis_client.hset(f"patient:{patient_id}", mapping=redis_patient_data)

        # Set expiration for patient data (24 hours)
        redis_client.expire(f"patient:{patient_id}", 86400)

        # TODO: Trigger A2A communication to Member 3's queue service
        # await a2a_messenger.send_event("patient_added_to_queue", {
        #     "patient_id": patient_id,
        #     "urgency": request.urgency,
        #     "queue_position": queue_position
        # })

        return WalkInResponse(
            success=True,
            patient_id=patient_id,
            queue_position=queue_position,
            estimated_wait_time=estimated_wait_time,
            check_in_time=datetime.now().isoformat()
        )

    except Exception as e:
        return WalkInResponse(
            success=False,
            error_message=f"Failed to process walk-in: {str(e)}"
        )


@router.get("/walkin/{patient_id}", response_model=PatientStatusResponse)
async def get_walkin_status(
        patient_id: str,
        redis_client: redis.Redis = Depends(get_redis)
):
    """Get current status of walk-in patient with real-time queue position."""

    patient_data = redis_client.hgetall(f"patient:{patient_id}")

    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get current queue position (0-indexed, so add 1)
    try:
        queue_position = redis_client.lpos("walkin_queue", patient_id)
        if queue_position is not None:
            queue_position += 1

        # Recalculate wait time based on current position
        if queue_position:
            urgency = int(patient_data.get("urgency", 3))
            base_wait_time = queue_position * 15
            urgency_multiplier = {5: 0.5, 4: 0.7, 3: 1.0, 2: 1.2, 1: 1.5}
            estimated_wait_time = int(base_wait_time * urgency_multiplier.get(urgency, 1.0))
        else:
            estimated_wait_time = 0  # Not in queue anymore

    except Exception:
        queue_position = None
        estimated_wait_time = None

    return PatientStatusResponse(
        patient_id=patient_id,
        status=patient_data.get("status", "unknown"),
        queue_position=queue_position,
        estimated_wait_time=estimated_wait_time,
        check_in_time=patient_data.get("check_in_time"),
        urgency=int(patient_data.get("urgency", 1)),
        last_updated=datetime.now().isoformat()
    )


@router.put("/walkin/{patient_id}/urgency")
async def update_walkin_urgency(
        patient_id: str,
        urgency: int,
        reason: Optional[str] = None,
        redis_client: redis.Redis = Depends(get_redis)
):
    """Update urgency level for walk-in patient and trigger queue reordering."""

    if urgency < 1 or urgency > 5:
        raise HTTPException(status_code=400, detail="Urgency must be between 1 and 5")

    patient_data = redis_client.hgetall(f"patient:{patient_id}")
    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")

    old_urgency = int(patient_data.get("urgency", 1))

    # Update urgency in patient data
    redis_client.hset(f"patient:{patient_id}", "urgency", urgency)
    redis_client.hset(f"patient:{patient_id}", "last_updated", datetime.now().isoformat())

    if reason:
        redis_client.hset(f"patient:{patient_id}", "urgency_update_reason", reason)

    # TODO: Trigger A2A communication to Member 3's queue service for reordering
    # await a2a_messenger.send_event("patient_urgency_updated", {
    #     "patient_id": patient_id,
    #     "old_urgency": old_urgency,
    #     "new_urgency": urgency,
    #     "reason": reason
    # })

    return {
        "patient_id": patient_id,
        "old_urgency": old_urgency,
        "new_urgency": urgency,
        "reason": reason,
        "updated_at": datetime.now().isoformat(),
        "message": "Urgency updated successfully"
    }


@router.delete("/walkin/{patient_id}")
async def cancel_walkin(
        patient_id: str,
        reason: str = "patient_cancelled",
        redis_client: redis.Redis = Depends(get_redis)
):
    """Cancel walk-in appointment and remove from queue."""

    patient_data = redis_client.hgetall(f"patient:{patient_id}")
    if not patient_data:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Remove from queue
    removed_count = redis_client.lrem("walkin_queue", 1, patient_id)

    # Update patient status
    redis_client.hset(f"patient:{patient_id}", "status", "cancelled")
    redis_client.hset(f"patient:{patient_id}", "cancellation_reason", reason)
    redis_client.hset(f"patient:{patient_id}", "cancelled_at", datetime.now().isoformat())

    # TODO: Trigger A2A communication to Member 3's services
    # await a2a_messenger.send_event("patient_cancelled", {
    #     "patient_id": patient_id,
    #     "reason": reason,
    #     "was_in_queue": removed_count > 0
    # })

    return {
        "patient_id": patient_id,
        "status": "cancelled",
        "reason": reason,
        "removed_from_queue": removed_count > 0,
        "cancelled_at": datetime.now().isoformat()
    }