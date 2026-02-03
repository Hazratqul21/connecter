"""
AI Processing Service for Call Intelligence
Handles transcription and analysis using OpenAI APIs
"""
import asyncio
import json
import httpx
from typing import Dict, Any, Optional
from io import BytesIO
from openai import AsyncOpenAI
from src.core.config import settings
from src.core.logging_config import get_logger
from src.core.exceptions import AIProcessingError, DatabaseError
from src.core.database import get_supabase

logger = get_logger(__name__)

# Initialize OpenAI client as singleton (reuse connection)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class AIService:
    """Service for AI-powered call transcription and analysis"""
    
    def __init__(self):
        self.whisper_model = settings.OPENAI_MODEL_WHISPER
        self.gpt_model = settings.OPENAI_MODEL_GPT
        self.audio_timeout = settings.AUDIO_DOWNLOAD_TIMEOUT
        self.max_audio_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024  # Convert to bytes
    
    async def download_audio(self, url: str) -> bytes:
        """
        Download audio file from URL with size validation
        
        Args:
            url: Audio file URL
            
        Returns:
            Audio file content as bytes
            
        Raises:
            AIProcessingError: If download fails or file too large
        """
        try:
            logger.info(f"Downloading audio from: {url}")
            
            async with httpx.AsyncClient(timeout=self.audio_timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content = response.content
                content_size = len(content)
                
                if content_size > self.max_audio_size:
                    raise AIProcessingError(
                        f"Audio file too large: {content_size / (1024*1024):.2f}MB "
                        f"(max: {settings.MAX_AUDIO_SIZE_MB}MB)"
                    )
                
                logger.info(f"Downloaded audio: {content_size / (1024*1024):.2f}MB")
                return content
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to download audio: {e}", exc_info=True)
            raise AIProcessingError(
                f"Audio download failed: {str(e)}",
                details={"url": url}
            )
    
    async def transcribe_audio(self, audio_content: bytes) -> str:
        """
        Transcribe audio using OpenAI Whisper
        
        Args:
            audio_content: Audio file content as bytes
            
        Returns:
            Transcribed text
            
        Raises:
            AIProcessingError: If transcription fails
        """
        try:
            logger.info("Starting Whisper transcription...")
            
            # Create file-like object (Whisper requires filename)
            audio_file = BytesIO(audio_content)
            audio_file.name = "recording.mp3"
            
            transcript_response = await openai_client.audio.transcriptions.create(
                model=self.whisper_model,
                file=audio_file
            )
            
            transcript_text = transcript_response.text
            logger.info(f"Transcription completed: {len(transcript_text)} characters")
            
            return transcript_text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            raise AIProcessingError(
                f"Audio transcription failed: {str(e)}"
            )
    
    async def analyze_call(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze call transcript using GPT
        
        Args:
            transcript: Transcribed call text
            
        Returns:
            Analysis results as dictionary
            
        Raises:
            AIProcessingError: If analysis fails
        """
        try:
            logger.info("Starting GPT analysis...")
            
            analysis_prompt = f"""
            Analyze this call transcript and provide structured insights.
            
            Transcript:
            "{transcript}"
            
            Return JSON with the following fields:
            - summary: Brief 2-3 sentence summary of the call
            - sentiment_score: Customer satisfaction rating (1-10, where 10 is very satisfied)
            - tags: List of relevant topics discussed (max 5 tags)
            - action_items: List of follow-up actions needed (if any)
            - urgency: Priority level for follow-up (1-10, where 10 is most urgent)
            - key_points: Main discussion points (max 3 bullet points)
            
            Be concise and objective in your analysis.
            """
            
            response = await openai_client.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": analysis_prompt}],
                response_format={"type": "json_object"}
            )
            
            analysis_json = json.loads(response.choices[0].message.content)
            logger.info("GPT analysis completed successfully")
            
            return analysis_json
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}", exc_info=True)
            raise AIProcessingError("Invalid JSON response from GPT")
            
        except Exception as e:
            logger.error(f"Call analysis failed: {e}", exc_info=True)
            raise AIProcessingError(f"Call analysis failed: {str(e)}")
    
    async def save_enrichment(
        self, 
        call_id: str, 
        transcript: str, 
        analysis: Dict[str, Any]
    ) -> None:
        """
        Save AI enrichment data to database
        
        Args:
            call_id: Binotel call UUID
            transcript: Full transcription text
            analysis: Analysis results from GPT
            
        Raises:
            DatabaseError: If database save fails
        """
        supabase = get_supabase()
        if not supabase:
            logger.warning("Supabase not configured, skipping enrichment save")
            return
        
        try:
            # First, resolve internal UUID from Binotel UUID
            logger.info(f"Looking up internal UUID for Binotel call: {call_id}")
            
            call_record = supabase.table("calls") \
                .select("id") \
                .eq("binotel_uuid", call_id) \
                .execute()
            
            if not call_record.data:
                raise DatabaseError(
                    f"Call record not found for binotel_uuid: {call_id}",
                    details={"binotel_uuid": call_id}
                )
            
            internal_uuid = call_record.data[0]['id']
            logger.info(f"Resolved internal UUID: {internal_uuid}")
            
            # Prepare enrichment data
            enrichment_data = {
                "call_id": internal_uuid,
                "transcription_text": transcript,
                "summary": analysis.get("summary"),
                "sentiment_score": analysis.get("sentiment_score"),
                "detected_topics": analysis.get("tags", []),
                "action_items": analysis.get("action_items", []),
                "urgency_score": analysis.get("urgency"),
                "key_points": analysis.get("key_points", [])
            }
            
            # Upsert to avoid duplicates
            supabase.table("call_enrichments").upsert(enrichment_data).execute()
            
            logger.info(f"Successfully saved enrichment for call: {call_id}")
            
        except Exception as e:
            logger.error(f"Failed to save enrichment: {e}", exc_info=True)
            raise DatabaseError(
                f"Failed to save enrichment: {str(e)}",
                details={"call_id": call_id}
            )
    
    async def process_call_intelligence(self, call_id: str, recording_url: str) -> None:
        """
        Complete AI processing pipeline for a call
        
        This is the main entry point for AI processing:
        1. Download audio
        2. Transcribe with Whisper
        3. Analyze with GPT
        4. Save to database
        
        Args:
            call_id: Binotel call UUID
            recording_url: URL to call recording
        """
        logger.info(
            f"Starting AI processing pipeline for call: {call_id}",
            extra={"call_id": call_id}
        )
        
        try:
            # Step 1: Download audio
            audio_content = await self.download_audio(recording_url)
            
            # Step 2: Transcribe
            transcript = await self.transcribe_audio(audio_content)
            
            # Step 3: Analyze
            analysis = await self.analyze_call(transcript)
            
            # Step 4: Save enrichment
            await self.save_enrichment(call_id, transcript, analysis)
            
            logger.info(
                f"AI processing completed successfully for call: {call_id}",
                extra={"call_id": call_id}
            )
            
        except AIProcessingError as e:
            logger.error(
                f"AI processing failed for call {call_id}: {e.message}",
                extra={"call_id": call_id}
            )
            raise
            
        except Exception as e:
            logger.error(
                f"Unexpected error in AI processing for call {call_id}: {e}",
                extra={"call_id": call_id},
                exc_info=True
            )
            raise AIProcessingError(
                f"Unexpected error in AI processing: {str(e)}",
                details={"call_id": call_id}
            )


# Global service instance
ai_service = AIService()


# Legacy compatibility function
async def process_call_intelligence(call_id: str, recording_url: str):
    """Legacy wrapper for backwards compatibility"""
    await ai_service.process_call_intelligence(call_id, recording_url)
