from fastapi import APIRouter

router = APIRouter()

@router.get("/appointments/test")
async def test_appointments():
    return {"message": "Appointments API working"}

@router.post("/appointments/lookup")
async def lookup_appointment():
    return {"success": True, "message": "Mock appointment lookup"}