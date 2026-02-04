"""
Call Processing Orchestrator
Coordinates the complete workflow: HelpDesk → Database → AI Processing
Ensures proper sequencing and error handling
"""
import asyncio
from typing import Dict, Any
from src.core.logging_config import get_logger
from src.core.exceptions import HelpDeskEddyError, DatabaseError, AIProcessingError
from src.services.helpdesk_service import helpdesk_service
from src.services.enrichment_service import enrichment_service
from src.services.ai_service import ai_service

logger = get_logger(__name__)


async def orchestrate_call_processing(
    call_summary_data: Dict[str, Any],
    binotel_payload: Dict[str, Any]
) -> None:
    """
    Master orchestration function for complete call processing
    
    Processing sequence:
    1. Send to HelpDeskEddy (synchronous, must succeed)
    2. Enrich and save to database (creates call record)
    3. AI processing (transcription + analysis)
    
    Each step is designed to be fault-tolerant:
    - HelpDeskEddy errors are logged but don't block database save
    - Database errors prevent AI processing (AI needs the call record)
    - AI errors are logged but don't affect earlier steps
    
    Args:
        call_summary_data: Parsed call data from webhook
        binotel_payload: Raw webhook payload
    """
    call_id = call_summary_data.get("uuid", "unknown")
    
    logger.info(
        f"=== Starting orchestration for call: {call_id} ===",
        extra={"call_id": call_id}
    )
    
    # Step 1: Send to HelpDeskEddy (Best effort)
    try:
        logger.info("Step 1: Sending to HelpDeskEddy...")
        await helpdesk_service.send_call_to_helpdesk(call_summary_data)
        logger.info("✓ HelpDeskEddy sync completed")
        
    except HelpDeskEddyError as e:
        # Log but continue - we still want to save to our database
        logger.error(
            f"HelpDeskEddy integration failed: {e.message}",
            extra={"call_id": call_id}
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in HelpDeskEddy sync: {e}",
            extra={"call_id": call_id},
            exc_info=True
        )
    
    # Step 2: Enrich and save to database (Critical)
    try:
        logger.info("Step 2: Enriching call record...")
        internal_uuid = await enrichment_service.enrich_call_record(
            call_summary_data,
            binotel_payload
        )
        
        if internal_uuid:
            logger.info(f"✓ Call record saved with UUID: {internal_uuid}")
        else:
            logger.warning("Database not configured, skipping enrichment")
            # If no database, we can't do AI processing either
            logger.info("=== Orchestration completed (no database) ===")
            return
            
    except DatabaseError as e:
        logger.error(
            f"Database enrichment failed: {e.message}",
            extra={"call_id": call_id}
        )
        # Cannot proceed to AI without database record
        logger.info("=== Orchestration terminated (database error) ===")
        return
        
    except Exception as e:
        logger.error(
            f"Unexpected error in enrichment: {e}",
            extra={"call_id": call_id},
            exc_info=True
        )
        logger.info("=== Orchestration terminated (unexpected error) ===")
        return
    
    # Step 3: AI Processing (Best effort, async)
    recording_url = call_summary_data.get("recording_url")
    
    if not recording_url:
        logger.info("No recording URL provided, skipping AI processing")
        logger.info("=== Orchestration completed (no recording) ===")
        return
    
    try:
        logger.info("Step 3: Starting AI processing...")
        await ai_service.process_call_intelligence(call_id, recording_url)
        logger.info("✓ AI processing completed")
        
    except AIProcessingError as e:
        # Log but don't fail the entire operation
        logger.error(
            f"AI processing failed: {e.message}",
            extra={"call_id": call_id}
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in AI processing: {e}",
            extra={"call_id": call_id},
            exc_info=True
        )
    
    logger.info(f"=== Orchestration completed for call: {call_id} ===")
