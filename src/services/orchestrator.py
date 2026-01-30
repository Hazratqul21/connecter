import logging
from fastapi import BackgroundTasks
from src.services.enrichment_service import enrichment_service
from src.services.ai_service import process_call_intelligence

logger = logging.getLogger(__name__)

async def orchestrate_call_processing(call_summary_data: dict, binotel_payload: dict):
    """
    Orchestrator to ensure correct order of operations:
    1. Enrichment (Saves Call to DB) -> This generates the UUID
    2. AI Analysis (Needs the UUID to save enrichment data)
    """
    try:
        call_uuid = call_summary_data.get("uuid") # This is Binotel ID
        logger.info(f"Orchestrator starting for {call_uuid}")

        # Step 1: Enrichment (Crucial to create the 'calls' record)
        # We await this so it finishes before AI starts looking for the record
        await enrichment_service.enrich_call_record(call_summary_data, binotel_payload)
        
        # Step 2: AI Analysis
        recording_url = call_summary_data.get("recording_url")
        if recording_url:
            # Note: We pass the Binotel ID, but the AI service will now need to look up the internal UUID
            # OR we updates enrichment_service to return the internal UUID and pass it here.
            # Let's update enrichment_service first to make this robust.
            await process_call_intelligence(call_uuid, recording_url)
        else:
            logger.info("No recording URL, skipping AI.")

    except Exception as e:
        logger.error(f"Orchestration failed for {call_summary_data.get('uuid')}: {e}", exc_info=True)
