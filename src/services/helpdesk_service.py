"""
HelpDeskEddy Integration Service
Handles synchronous communication with HelpDeskEddy CRM
"""
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from src.core.config import settings
from src.core.logging_config import get_logger
from src.core.exceptions import HelpDeskEddyError

logger = get_logger(__name__)


class HelpDeskEddyService:
    """Service for sending call data to HelpDeskEddy CRM"""
    
    def __init__(self):
        self.base_url = settings.HELPDESKEDDY_URL
        self.timeout = settings.HELPDESKEDDY_TIMEOUT
        self.max_retries = settings.MAX_WEBHOOK_RETRIES
    
    def _prepare_hde_payload(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Binotel call data into HelpDeskEddy format
        
        Args:
            call_data: Parsed Binotel call data
            
        Returns:
            HelpDeskEddy formatted payload
        """
        return {
            "call_id": call_data.get("uuid", "unknown"),
            "phone": call_data.get("phone", ""),
            "direction": call_data.get("direction", "incoming"),
            "status": call_data.get("status", "completed"),
            "duration": call_data.get("duration", 0),
            "recording_url": call_data.get("recording_url", ""),
            "agent_extension": call_data.get("extension", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_call_to_helpdesk(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send call data to HelpDeskEddy with retry logic
        
        Args:
            call_data: Call data dictionary
            
        Returns:
            HelpDeskEddy API response
            
        Raises:
            HelpDeskEddyError: If all retry attempts fail
        """
        payload = self._prepare_hde_payload(call_data)
        
        logger.info(
            f"Sending call {call_data.get('uuid')} to HelpDeskEddy",
            extra={"call_id": call_data.get('uuid')}
        )
        
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.base_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    response.raise_for_status()
                    
                    logger.info(
                        f"Successfully sent call to HelpDeskEddy (attempt {attempt})",
                        extra={"call_id": call_data.get('uuid')}
                    )
                    
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    f"HelpDeskEddy returned error {e.response.status_code} "
                    f"(attempt {attempt}/{self.max_retries})",
                    extra={"call_id": call_data.get('uuid'), "status_code": e.response.status_code}
                )
                
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"Network error sending to HelpDeskEddy (attempt {attempt}/{self.max_retries}): {e}",
                    extra={"call_id": call_data.get('uuid')}
                )
                
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        error_message = f"Failed to send call to HelpDeskEddy after {self.max_retries} attempts"
        logger.error(
            error_message,
            extra={"call_id": call_data.get('uuid'), "last_error": str(last_error)}
        )
        
        raise HelpDeskEddyError(
            message=error_message,
            details={"call_id": call_data.get('uuid'), "last_error": str(last_error)}
        )


# Global service instance
helpdesk_service = HelpDeskEddyService()
