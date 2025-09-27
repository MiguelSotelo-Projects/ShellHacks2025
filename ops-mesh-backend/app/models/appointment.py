from pydantic import BaseModel
from typing import Optional

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