from fastapi import APIRouter

router = APIRouter()

@router.post("/checkin")
async def process_checkin():
    return {"success": True, "message": "Mock checkin"}