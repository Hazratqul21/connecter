import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from extract_call_data import CallData # Assuming this type exists or dict
from src.core.database import get_supabase
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class EnrichmentService:
    def __init__(self):
        self.supabase = get_supabase()
        self.settings = get_settings()

    async def get_or_create_customer(self, phone: str, name: Optional[str] = None) -> Optional[str]:
        """
        Find customer by phone. If not exists, create minimal profile.
        Returns customer_id (UUID).
        """
        if not self.supabase: return None
        
        try:
            # 1. Search
            response = self.supabase.table("customers").select("id, full_name").eq("phone_number", phone).execute()
            if response.data:
                return response.data[0]["id"]
            
            # 2. Create if not found
            new_customer = {
                "phone_number": phone,
                "full_name": name or "Unknown Customer",
                "tags": ["new"]
            }
            response = self.supabase.table("customers").insert(new_customer).execute()
            if response.data:
                logger.info(f"Created new customer for {phone}")
                return response.data[0]["id"]
                
        except Exception as e:
            logger.error(f"Error in customer lookup: {e}")
            return None

    async def get_agent_id(self, extension: str) -> Optional[str]:
        """Resolve agent extension to UUID."""
        if not self.supabase: return None
        try:
            response = self.supabase.table("agents").select("id").eq("extension_number", extension).execute()
            if response.data:
                return response.data[0]["id"]
        except Exception as e:
            logger.error(f"Error in agent lookup: {e}")
        return None

    async def enrich_call_record(self, call_data: Dict[str, Any], binotel_payload: Dict[str, Any]):
        """
        Main pipeline to enrich raw webhook data and save to 'calls' table.
        This runs BEFORE sending to HDE if possible, or Async.
        """
        if not self.supabase:
            logger.warning("Supabase client not active. Skipping enrichment.")
            return

        try:
            phone = call_data.get("phone")
            extension = call_data.get("extension")
            
            # 1. Parallel Lookups
            customer_id, agent_id = await asyncio.gather(
                self.get_or_create_customer(phone),
                self.get_agent_id(extension)
            )

            # 2. Prepare Call Record
            raw_record = {
                "binotel_uuid": call_data.get("uuid"),
                "direction": call_data.get("direction"),
                "status": call_data.get("status"),
                "phone_number": phone,
                "agent_extension": extension,
                "agent_id": agent_id,
                "customer_id": customer_id,
                "duration_seconds": call_data.get("duration", 0),
                "recording_url": call_data.get("recording_url"),
                "started_at": datetime.now().isoformat(), # Ideally parse from payload
            }

            # 3. Upsert into Supabase
            # We utilize upsert based on binotel_uuid to avoid duplicates
            self.supabase.table("calls").upsert(raw_record, on_conflict="binotel_uuid").execute()
            logger.info(f"Enriched call record saved: {raw_record.get('binotel_uuid')}")
            
            # 4. Refresh Daily Stats (Async usually, but fast enough here)
            # We can call the SQL function we created
            self.supabase.rpc("refresh_analytics_agent_daily", {"p_days_back": 1}).execute()

        except Exception as e:
            logger.error(f"Enrichment Pipeline Failed: {e}", exc_info=True)

enrichment_service = EnrichmentService()
