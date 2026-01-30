import os
import json
import logging
import asyncio
from openai import AsyncOpenAI
import httpx
from src.core.config import get_settings
from src.core.database import get_supabase

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize OpenAI Client (Global to reuse connection)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def download_audio_content(url: str) -> bytes:
    """Download audio file into memory (limit size if needed)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.content

async def process_call_intelligence(call_id: str, audio_url: str):
    """
    This function runs in the background AFTER the webhook returns 200 OK.
    WARNING: On Vercel, this must finish before the lambda spins down (approx 10-60s).
    """
    logger.info(f"START: AI Processing for Call {call_id}")
    
    try:
        # 1. Download Audio
        logger.info(f"Downloading audio from {audio_url}...")
        audio_bytes = await download_audio_content(audio_url)
        
        # 2. Transcribe (Whisper)
        # OpenAI requires a file-like object with a name
        logger.info("Transcribing with Whisper...")
        from io import BytesIO
        audio_file = BytesIO(audio_bytes)
        audio_file.name = "recording.mp3" 

        transcript_obj = await openai_client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        transcript_text = transcript_obj.text
        logger.info(f"Transcription complete (len={len(transcript_text)})")

        # 3. Analyze (GPT-4o)
        logger.info("Analyzing with GPT-4o...")
        prompt = f"""
        Analyze this call transcript:
        "{transcript_text}"
        
        Return JSON with:
        - summary (string)
        - sentiment_score (1-10)
        - tags (list of strings)
        - action_items (list of strings)
        - urgency (1-10)
        """
        
        chat_response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        analysis_json = json.loads(chat_response.choices[0].message.content)
        
        # 4. Save to Supabase
        # We need to resolve the internal UUID from the calls table using the Binotel ID
        supabase = get_supabase()
        if supabase:
            # Lookup UUID
            call_record = supabase.table("calls").select("id").eq("binotel_uuid", call_id).execute()
            if not call_record.data:
                logger.error(f"Call record not found for binotel_uuid {call_id}. Cannot save enrichment.")
                return
            
            internal_uuid = call_record.data[0]['id']

            enrichment_data = {
                "call_id": internal_uuid, 
                "transcription_text": transcript_text,
                "summary": analysis_json.get("summary"),
                "sentiment_score": analysis_json.get("sentiment_score"),
                "detected_topics": analysis_json.get("tags"),
                "action_items": analysis_json.get("action_items"),
                "urgency_score": analysis_json.get("urgency")
            }
            
            # Upsert into enrichment table
            # Upsert into enrichment table
            supabase.table("call_enrichments").upsert(enrichment_data).execute()
            logger.info("Saved analysis to Supabase.")
            
    except Exception as e:
        logger.error(f"AI Processing FAILED for {call_id}: {str(e)}", exc_info=True)
