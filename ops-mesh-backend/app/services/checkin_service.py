from typing import Dict, Any
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential


class CheckInService:
    def __init__(self):
        self.room_assignments = {
            "Cardiology": ["Room 305", "Room 306", "Room 307"],
            "General": ["Room 201", "Room 202", "Room 203"],
            "Pediatrics": ["Room 150", "Room 151", "Room 152"],
            "Emergency": ["ER Bay 1", "ER Bay 2", "ER Bay 3"]
        }
        self.assigned_rooms = set()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_appointment_checkin(self, patient_id: str, confirmation_code: str) -> Dict[str, Any]:
        try:
            mock_appointments = {
                "APPT123": {
                    "appointment_id": "apt_001",
                    "patient_name": "John Doe",
                    "department": "Cardiology",
                    "provider": "Dr. Smith",
                    "appointment_time": "2025-09-27T14:30:00"
                },
                "APPT456": {
                    "appointment_id": "apt_002",
                    "patient_name": "Jane Smith",
                    "department": "General",
                    "provider": "Dr. Johnson",
                    "appointment_time": "2025-09-27T15:00:00"
                }
            }

            appointment_data = mock_appointments.get(confirmation_code)

            if appointment_data:
                return {"success": True, "appointment_data": appointment_data}
            else:
                return {"success": False, "error_message": "Invalid confirmation code or appointment not found"}

        except Exception as e:
            return {"success": False, "error_message": f"Check-in processing failed: {str(e)}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_walkin_checkin(self, patient_id: str, patient_data: Dict) -> Dict[str, Any]:
        try:
            valid_statuses = ["waiting", "intake_complete"]
            current_status = patient_data.get("status")

            if current_status not in valid_statuses:
                return {"success": False,
                        "error_message": f"Patient not eligible for check-in. Current status: {current_status}"}

            return {"success": True, "patient_data": patient_data}

        except Exception as e:
            return {"success": False, "error_message": f"Walk-in check-in failed: {str(e)}"}

    async def assign_room(self, department: str, provider: str = None) -> str:
        available_rooms = self.room_assignments.get(department, ["Room 100"])

        for room in available_rooms:
            if room not in self.assigned_rooms:
                self.assigned_rooms.add(room)
                return room

        return available_rooms[0]

    async def release_room(self, room: str):
        self.assigned_rooms.discard(room)