"""
Webhook Payload Validation and Parsing Module
Handles incoming Binotel webhook data with robust error handling
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from src.core.config import settings
from src.core.logging_config import get_logger
from src.core.exceptions import WebhookValidationError

logger = get_logger(__name__)


class BinotelCallData(BaseModel):
    """Structured model for Binotel call data"""
    
    general_call_id: str = Field(..., alias="generalCallID")
    request_type: str = Field(..., alias="requestType")
    direction: Optional[str] = None
    status: Optional[str] = None
    external_number: Optional[str] = Field(None, alias="externalNumber")
    internal_number: Optional[str] = Field(None, alias="internalNumber")
    billsec: Optional[int] = 0
    recording_url: Optional[str] = Field(None, alias="recordingUrl")
    link_to_call_record: Optional[str] = Field(None, alias="linkToCallRecordInMyBusiness")
    
    class Config:
        populate_by_name = True
        
    @validator('billsec', pre=True, always=True)
    def parse_billsec(cls, v):
        """Convert billsec to integer, default to 0 if invalid"""
        if v is None:
            return 0
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0
    
    @property
    def final_recording_url(self) -> str:
        """Get the actual recording URL from available fields"""
        return self.recording_url or self.link_to_call_record or ""
    
    @property
    def phone_number(self) -> str:
        """Get the external phone number"""
        return self.external_number or "unknown"
    
    @property
    def agent_extension(self) -> str:
        """Get the internal extension/agent number"""
        return self.internal_number or ""


def extract_field_from_payload(payload: Dict[str, Any], field_name: str) -> Optional[Any]:
    """
    Extract field from payload with multiple fallback strategies
    
    Binotel sometimes sends fields as:
    - Direct key: {"generalCallID": "123"}
    - Form-encoded: {"callDetails[generalCallID]": "123"}
    
    Args:
        payload: Raw webhook payload
        field_name: Field name to extract
        
    Returns:
        Field value or None
    """
    # Try direct key first
    if field_name in payload:
        return payload[field_name]
    
    # Try form-encoded format
    form_key = f"callDetails[{field_name}]"
    if form_key in payload:
        return payload[form_key]
    
    return None


def validate_webhook_event(payload: Dict[str, Any]) -> bool:
    """
    Validate if webhook event should be processed
    
    Args:
        payload: Raw webhook payload
        
    Returns:
        True if event should be processed, False otherwise
    """
    request_type = extract_field_from_payload(payload, "requestType")
    
    if not request_type:
        logger.warning("Webhook missing requestType field")
        return False
    
    if request_type not in settings.VALID_EVENT_TYPES:
        logger.info(f"Ignoring event type: {request_type}")
        return False
    
    # Additional validation: must have generalCallID
    general_call_id = extract_field_from_payload(payload, "generalCallID")
    if not general_call_id:
        logger.warning("Webhook missing generalCallID")
        return False
    
    return True


def parse_binotel_webhook(payload: Dict[str, Any]) -> BinotelCallData:
    """
    Parse and validate Binotel webhook payload
    
    Args:
        payload: Raw webhook payload
        
    Returns:
        Validated BinotelCallData instance
        
    Raises:
        WebhookValidationError: If payload validation fails
    """
    try:
        # Extract all fields with fallback logic
        parsed_data = {
            "generalCallID": extract_field_from_payload(payload, "generalCallID"),
            "requestType": extract_field_from_payload(payload, "requestType"),
            "direction": extract_field_from_payload(payload, "direction"),
            "status": extract_field_from_payload(payload, "status"),
            "externalNumber": extract_field_from_payload(payload, "externalNumber"),
            "internalNumber": extract_field_from_payload(payload, "internalNumber"),
            "billsec": extract_field_from_payload(payload, "billsec"),
            "recordingUrl": extract_field_from_payload(payload, "recordingUrl"),
            "linkToCallRecordInMyBusiness": extract_field_from_payload(payload, "linkToCallRecordInMyBusiness"),
        }
        
        # Validate using Pydantic model
        return BinotelCallData(**parsed_data)
        
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}", exc_info=True)
        raise WebhookValidationError(
            message="Invalid webhook payload format",
            details={"error": str(e), "payload": payload}
        )
