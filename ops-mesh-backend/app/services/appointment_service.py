from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential


class AppointmentService:
    def __init__(self):
        self.mock_appointments = {
            "APPT123": {
                "appointment_id": "apt_001",
                "patient_name": "John Doe",
                "appointment_time": "2025-09-27T14:30:00",
                "department": "Cardiology",
                "provider": "Dr. Smith",
                "status": "confirmed"
            },
            "APPT456": {
                "appointment_id": "apt_002",
                "patient_name": "Jane Smith",
                "appointment_time": "2025-09-27T15:00:00",
                "department": "General",
                "provider": "Dr. Johnson",
                "status": "confirmed"
            }
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def lookup_appointment(self, confirmation_code: str):
        try:
            from app.models.appointment import AppointmentLookupResponse, AppointmentData

            appointment_data = self.mock_appointments.get(confirmation_code)

            if appointment_data:
                appointment = AppointmentData(**appointment_data)
                return AppointmentLookupResponse(success=True, appointment=appointment)
            else:
                return AppointmentLookupResponse(success=False, error_message="Appointment not found")

        except Exception as e:
            from app.models.appointment import AppointmentLookupResponse
            return AppointmentLookupResponse(success=False, error_message=f"Service error: {str(e)}")