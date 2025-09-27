from fastapi import APIRouter

router = APIRouter()

@router.get("/queue")
async def get_queue():
    return {"queue": [], "message": "Mock queue"}