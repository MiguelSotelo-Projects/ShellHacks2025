"""
Check-in API routes - Member 2 responsibility
Handles final check-in orchestration using Google ADK agents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Optional
import redis
from databases import Database
from datetime import datetime

from app.api.deps import get_database, get_redis
from app.services.checkin_service import CheckInService

router = APIRouter()

# Initialize service
checkin_service = CheckInService()


# Request/Response Models
class CheckInRequest(BaseModel):
    patient_id: str
    patient_type: str  # "appointment" or "walkin"
    confirmation_code: Optional[str] = None

    @validator('patient_type')
    def validate_patient_type(cls, v):
        if v not in ["appointment", "walkin"]:
            raise ValueError('Patient type must be "appointment" or "walkin"')
        return v

    @validator('confirmation_code')
    def validate_confirmation_code(cls, v, values):
        if values.get('patient_type') == 'appointment' and not v:
            raise ValueError('Confirmation code required for appointment check-in')
        return v


class CheckInResponse(BaseModel):
    success: bool
    patient_id: str
    check_in_time: Optional[str] = None
    room_assignment: Optional[str] = None
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None
    next_steps: Optional[str] = None
    error_message: Optional[str] = None


class CheckInStatusResponse(BaseModel):
    patient_id: str
    status: str
    check_in_time: Optional[str] = None
    room_assignment: Optional[str] = None
    provider: Optional[str] = None
    department: Optional[str] = None
    queue_position: Optional[int] = None
    estimated_wait_time: Optional[int] = None
    last_updated: str


@router.post("/checkin", response_model=CheckInResponse)
async def process_checkin(
        request: CheckInRequest,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """
    Process final patient check-in using Google ADK orchestration.

    Coordinates between appointment/walk-in systems and room assignment.
    Triggers A2A communication for dashboard updates.
    """

    try:
        check_in_time = datetime.now().isoformat()

        if request.patient_type == "appointment":
            # Handle appointment check-in
            result = await checkin_service.process_appointment_checkin(
                request.patient_id,
                request.confirmation_code
            )

            if not result["success"]:
                return CheckInResponse(
                    success=False,
                    patient_id=request.patient_id,
                    error_message=result["error_message"]
                )

            appointment_data = result["appointment_data"]

            # Assign room based on department
            room_assignment = await checkin_service.assign_room(
                appointment_data["department"],
                appointment_data["provider"]
            )

            # Update appointment status
            redis_client.hset(f"appointment:{request.patient_id}", mapping={
                "status": "checked-in",
                "check_in_time": check_in_time,
                "room_assignment": room_assignment
            })

            next_steps = f"Please proceed to {room_assignment}. {appointment_data['provider']} will see you shortly."

            # TODO: Trigger A2A communication to Member 3's dashboard
            # await a2a_messenger.send_event("appointment_checked_in", {
            #     "patient_id": request.patient_id,
            #     "appointment_id": appointment_data["appointment_id"],
            #     "room": room_assignment,
            #     "provider": appointment_data["provider"]
            # })

            return CheckInResponse(
                success=True,
                patient_id=request.patient_id,
                check_in_time=check_in_time,
                room_assignment=room_assignment,
                next_steps=next_steps
            )

        elif request.patient_type == "walkin":
            # Handle walk-in check-in
            patient_data = redis_client.hgetall(f"patient:{request.patient_id}")

            if not patient_data:
                return CheckInResponse(
                    success=False,
                    patient_id=request.patient_id,
                    error_message="Walk-in patient not found"
                )

            # Process through check-in service
            result = await checkin_service.process_walkin_checkin(request.patient_id, patient_data)

            if not result["success"]:
                return CheckInResponse(
                    success=False,
                    patient_id=request.patient_id,
                    error_message=result["error_message"]
                )

            # Get current queue position
            queue_position = redis_client.lpos("walkin_queue", request.patient_id)
            if queue_position is not None:
                queue_position += 1

            # Calculate wait time
            urgency = int(patient_data.get("urgency", 3))
            estimated_wait_time = queue_position * 15 if queue_position else 0
            urgency_multiplier = {5: 0.5, 4: 0.7, 3: 1.0, 2: 1.2, 1: 1.5}
            estimated_wait_time = int(estimated_wait_time * urgency_multiplier.get(urgency, 1.0))

            # Update patient status
            redis_client.hset(f"patient:{request.patient_id}", mapping={
                "status": "checked-in",
                "check_in_time": check_in_time,
                "queue_position": queue_position or 0,
                "estimated_wait_time": estimated_wait_time
            })

            # Assign waiting area based on urgency
            if urgency >= 4:
                waiting_area = "Priority Waiting Area"
            else:
                waiting_area = "General Waiting Area"

            next_steps = f"Please take a seat in {waiting_area}. You will be called when ready."

            # TODO: Trigger A2A communication to Member 3's queue service
            # await a2a_messenger.send_event("walkin_checked_in", {
            #     "patient_id": request.patient_id,
            #     "urgency": urgency,
            #     "queue_position": queue_position,
            #     "waiting_area": waiting_area
            # })

            return CheckInResponse(
                success=True,
                patient_id=request.patient_id,
                check_in_time=check_in_time,
                queue_position=queue_position,
                estimated_wait_time=estimated_wait_time,
                next_steps=next_steps
            )

    except Exception as e:
        return CheckInResponse(
            success=False,
            patient_id=request.patient_id,
            error_message=f"Check-in failed: {str(e)}"
        )


@router.get("/checkin/status/{patient_id}", response_model=CheckInStatusResponse)
async def get_checkin_status(
        patient_id: str,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """Get comprehensive check-in status for a patient."""

    # Check both appointment and walk-in data
    appointment_data = redis_client.hgetall(f"appointment:{patient_id}")
    patient_data = redis_client.hgetall(f"patient:{patient_id}")

    if appointment_data:
        # This is an appointment patient
        return CheckInStatusResponse(
            patient_id=patient_id,
            status=appointment_data.get("status", "unknown"),
            check_in_time=appointment_data.get("check_in_time"),
            room_assignment=appointment_data.get("room_assignment"),
            provider=appointment_data.get("provider"),
            department=appointment_data.get("department"),
            last_updated=datetime.now().isoformat()
        )
    elif patient_data:
        # This is a walk-in patient
        queue_position = redis_client.lpos("walkin_queue", patient_id)
        if queue_position is not None:
            queue_position += 1

        return CheckInStatusResponse(
            patient_id=patient_id,
            status=patient_data.get("status", "unknown"),
            check_in_time=patient_data.get("check_in_time"),
            queue_position=queue_position,
            estimated_wait_time=int(patient_data.get("estimated_wait_time", 0)),
            last_updated=datetime.now().isoformat()
        )
    else:
        raise HTTPException(status_code=404, detail="Patient not found")


@router.put("/checkin/{patient_id}/complete")
async def complete_checkin(
        patient_id: str,
        notes: Optional[str] = None,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """Mark patient check-in as complete and ready for provider."""

    completion_time = datetime.now().isoformat()

    # Check if appointment or walk-in
    appointment_data = redis_client.hgetall(f"appointment:{patient_id}")
    patient_data = redis_client.hgetall(f"patient:{patient_id}")

    if appointment_data:
        # Update appointment status
        redis_client.hset(f"appointment:{patient_id}", mapping={
            "status": "ready-for-provider",
            "completion_time": completion_time,
            "notes": notes or ""
        })
        patient_type = "appointment"
    elif patient_data:
        # Update walk-in status and remove from queue
        redis_client.hset(f"patient:{patient_id}", mapping={
            "status": "ready-for-provider",
            "completion_time": completion_time,
            "notes": notes or ""
        })

        # Remove from queue since ready for provider
        redis_client.lrem("walkin_queue", 1, patient_id)
        patient_type = "walkin"
    else:
        raise HTTPException(status_code=404, detail="Patient not found")

    # TODO: Trigger A2A communication to notify provider and update dashboard
    # await a2a_messenger.send_event("patient_ready_for_provider", {
    #     "patient_id": patient_id,
    #     "patient_type": patient_type,
    #     "completion_time": completion_time,
    #     "notes": notes
    # })

    return {
        "patient_id": patient_id,
        "status": "ready-for-provider",
        "patient_type": patient_type,
        "completion_time": completion_time,
        "notes": notes,
        "message": "Patient ready for provider"
    }


@router.post("/checkin/batch")
async def batch_checkin_status(
        patient_ids: list[str],
        redis_client: redis.Redis = Depends(get_redis)
):
    """Get check-in status for multiple patients (useful for dashboard)."""

    results = []

    for patient_id in patient_ids:
        appointment_data = redis_client.hgetall(f"appointment:{patient_id}")
        patient_data = redis_client.hgetall(f"patient:{patient_id}")

        if appointment_data:
            results.append({
                "patient_id": patient_id,
                "type": "appointment",
                "status": appointment_data.get("status", "unknown"),
                "check_in_time": appointment_data.get("check_in_time"),
                "room_assignment": appointment_data.get("room_assignment")
            })
        elif patient_data:
            queue_position = redis_client.lpos("walkin_queue", patient_id)
            results.append({
                "patient_id": patient_id,
                "type": "walkin",
                "status": patient_data.get("status", "unknown"),
                "check_in_time": patient_data.get("check_in_time"),
                "queue_position": (queue_position + 1) if queue_position is not None else None
            })
        else:
            results.append({
                "patient_id": patient_id,
                "type": "unknown",
                "status": "not_found"
            })

    return {
        "results": results,
        "total_patients": len(patient_ids),
        "timestamp": datetime.now().isoformat()
    }