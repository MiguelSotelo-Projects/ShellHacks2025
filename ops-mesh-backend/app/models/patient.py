from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WalkInRequest(BaseModel):
    name: str
    phone: Optional[str] = None
    reason: str
    urgency: int  # 1-5 scale
    preferred_department: Optional[str] = None

class PatientData(BaseModel):
    patient_id: str
    name: str
    type: str  # "appointment" or "walkin"
    status: str
    check_in_time: Optional[datetime] = None
    urgency: Optional[int] = None