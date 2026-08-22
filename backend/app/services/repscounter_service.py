import logging
from typing import Any, Dict
from app.repositories.firebase_repo import FirebaseRepository

logger = logging.getLogger(__name__)

class RepsCounterService:
    def __init__(self, repository: FirebaseRepository):
        self.repository = repository

    async def process_request(self, card_id: str, machine_id: str) -> Dict[str, Any]:
        latest_log = await self.repository.get_latest_machine_log(machine_id, card_id)
        
        if latest_log:
            return {
                "machine_id": machine_id,
                "card_id": card_id,
                "weight": latest_log.get("weight", 0),
                "reps": latest_log.get("reps", 0)
            }
        
        return {
            "machine_id": machine_id,
            "card_id": card_id,
            "weight": 0,
            "reps": 0
        }

    async def process_result(self, card_id: str, machine_id: str, weight: int, reps: int) -> Dict[str, Any]:
        log = await self.repository.add_machine_log(machine_id, card_id, weight, reps)
        return log