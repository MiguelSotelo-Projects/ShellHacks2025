from fastapi import APIRouter

router = APIRouter()

@router.post("/walkin")
async def submit_walkin():
    return {"success": True, "message": "Mock walkin submission"}