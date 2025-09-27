"""
Appointment API routes - Member 2 responsibility
Handles appointment lookup and validation using Google ADK agents.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import redis
from databases import Database

from app.api.deps import get_database, get_redis
from app.services.appointment_service import AppointmentService

router = APIRouter()

# Initialize service
appointment_service = AppointmentService()


# Request/Response Models
class AppointmentLookupRequest(BaseModel):
    confirmation_code: str


class AppointmentData(BaseModel):
    appointment_id: str
    patient_name: str
    appointment_time: str
    department: str
    provider: str
    status: str = "confirmed"


class AppointmentLookupResponse(BaseModel):
    success: bool
    appointment: Optional[AppointmentData] = None
    error_message: Optional[str] = None


@router.post("/appointments/lookup", response_model=AppointmentLookupResponse)
async def lookup_appointment(
        request: AppointmentLookupRequest,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """
    Lookup appointment by confirmation code using Google ADK agent.

    Uses retry logic and caches results for performance.
    Implements fallback logic for invalid codes.
    """

    # Check Redis cache first
    cache_key = f"appointment:{request.confirmation_code}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        # Return cached result
        import json
        cached_data = json.loads(cached_result)
        if cached_data["success"]:
            return AppointmentLookupResponse(
                success=True,
                appointment=AppointmentData(**cached_data["appointment"])
            )
        else:
            return AppointmentLookupResponse(
                success=False,
                error_message=cached_data["error_message"]
            )

    # Call service layer with Google ADK integration
    result = await appointment_service.lookup_appointment(request.confirmation_code)

    # Cache the result for 5 minutes
    import json
    cache_data = {
        "success": result.success,
        "appointment": result.appointment.dict() if result.appointment else None,
        "error_message": result.error_message
    }
    redis_client.setex(cache_key, 300, json.dumps(cache_data))

    return result


@router.get("/appointments/{appointment_id}")
async def get_appointment_details(
        appointment_id: str,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """Get detailed appointment information by ID."""

    # Check cache first
    cache_key = f"appointment_details:{appointment_id}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        import json
        return json.loads(cached_result)

    # TODO: Implement database lookup
    # For now, mock response
    appointment_details = {
        "appointment_id": appointment_id,
        "status": "confirmed",
        "patient_name": "John Doe",
        "appointment_time": "2025-09-27T14:30:00",
        "department": "Cardiology",
        "provider": "Dr. Smith",
        "notes": "Regular checkup",
        "room_assignment": None,
        "check_in_status": "pending"
    }

    # Cache for 10 minutes
    import json
    redis_client.setex(cache_key, 600, json.dumps(appointment_details))

    return appointment_details


@router.put("/appointments/{appointment_id}/status")
async def update_appointment_status(
        appointment_id: str,
        status: str,
        db: Database = Depends(get_database),
        redis_client: redis.Redis = Depends(get_redis)
):
    """Update appointment status and trigger A2A communication."""

    if status not in ["confirmed", "checked-in", "in-progress", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Update in database (TODO: implement actual DB update)
    update_time = datetime.now().isoformat()

    # Update Redis cache
    cache_key = f"appointment_details:{appointment_id}"
    cached_data = redis_client.get(cache_key)

    if cached_data:
        import json
        appointment_data = json.loads(cached_data)
        appointment_data["status"] = status
        appointment_data["last_updated"] = update_time
        redis_client.setex(cache_key, 600, json.dumps(appointment_data))

    # TODO: Trigger A2A communication to Member 3's services
    # await a2a_messenger.send_event("appointment_status_updated", {
    #     "appointment_id": appointment_id,
    #     "status": status,
    #     "updated_at": update_time
    # })

    return {
        "appointment_id": appointment_id,
        "status": status,
        "updated_at": update_time,
        "message": "Status updated successfully"
    }


@router.post("/appointments/validate-code")
async def validate_confirmation_code(
        confirmation_code: str,
        redis_client: redis.Redis = Depends(get_redis)
):
    """Quick validation of confirmation code format and existence."""

    # Basic format validation
    if len(confirmation_code) < 4 or not confirmation_code.isalnum():
        return {
            "valid": False,
            "reason": "Invalid confirmation code format"
        }

    # Check if code exists (using service)
    result = await appointment_service.lookup_appointment(confirmation_code)

    return {
        "valid": result.success,
        "reason": result.error_message if not result.success else "Valid confirmation code"
    }