from typing import Dict, Any
import uuid
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential


class WalkInService:
    def __init__(self):
        pass

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def process_walkin_intake(self, walkin_request) -> Dict[str, Any]:
        try:
            if len(walkin_request.name.strip()) < 2:
                return {"success": False, "error_message": "Invalid patient name"}

            if walkin_request.urgency < 1 or walkin_request.urgency > 5:
                return {"success": False, "error_message": "Urgency must be between 1 and 5"}

            patient_id = str(uuid.uuid4())

            patient_data = {
                "patient_id": patient_id,
                "name": walkin_request.name,
                "reason": walkin_request.reason,
                "urgency": walkin_request.urgency,
                "phone": walkin_request.phone or "",
                "preferred_department": walkin_request.preferred_department or "General",
                "intake_time": datetime.now().isoformat(),
                "status": "intake_complete"
            }

            return {"success": True, "patient_data": patient_data}

        except Exception as e:
            return {"success": False, "error_message": f"Intake processing failed: {str(e)}"}