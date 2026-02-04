"""
Call Enrichment Service
Handles customer/agent lookup and call record creation in database
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from src.core.database import get_supabase
from src.core.config import settings
from src.core.logging_config import get_logger
from src.core.exceptions import DatabaseError

logger = get_logger(__name__)


class EnrichmentService:
    """Service for enriching call records with customer and agent data"""
    
    def __init__(self):
        self.supabase = get_supabase()
    
    async def get_or_create_customer(
        self, 
        phone: str, 
        name: Optional[str] = None
    ) -> Optional[str]:
        """
        Find existing customer by phone or create new customer profile
        
        Args:
            phone: Customer phone number
            name: Optional customer name
            
        Returns:
            Customer UUID or None if database unavailable
            
        Raises:
            DatabaseError: If database operation fails
        """
        if not self.supabase:
            logger.warning("Supabase not configured, skipping customer lookup")
            return None
        
        try:
            # Search for existing customer
            logger.info(f"Searching for customer with phone: {phone}")
            
            response = self.supabase.table("customers") \
                .select("id, full_name") \
                .eq("phone_number", phone) \
                .execute()
            
            if response.data:
                customer_id = response.data[0]["id"]
                logger.info(f"Found existing customer: {customer_id}")
                return customer_id
            
            # Create new customer if not found
            logger.info(f"Creating new customer for phone: {phone}")
            
            new_customer = {
                "phone_number": phone,
                "full_name": name or "Unknown Customer",
                "tags": ["new", "from_binotel"],
                "created_via": "connecter_middleware"
            }
            
            response = self.supabase.table("customers") \
                .insert(new_customer) \
                .execute()
            
            if response.data:
                customer_id = response.data[0]["id"]
                logger.info(f"Created new customer: {customer_id}")
                return customer_id
            
            logger.warning("Failed to create customer (no data returned)")
            return None
            
        except Exception as e:
            logger.error(f"Customer lookup/create failed: {e}", exc_info=True)
            raise DatabaseError(
                f"Customer operation failed: {str(e)}",
                details={"phone": phone}
            )
    
    async def get_agent_id(self, extension: str) -> Optional[str]:
        """
        Resolve agent extension to internal UUID
        
        Args:
            extension: Agent extension number
            
        Returns:
            Agent UUID or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        if not self.supabase or not extension:
            return None
        
        try:
            logger.info(f"Looking up agent with extension: {extension}")
            
            response = self.supabase.table("agents") \
                .select("id, full_name") \
                .eq("extension_number", extension) \
                .execute()
            
            if response.data:
                agent_id = response.data[0]["id"]
                logger.info(f"Found agent: {agent_id}")
                return agent_id
            
            logger.warning(f"Agent not found for extension: {extension}")
            return None
            
        except Exception as e:
            logger.error(f"Agent lookup failed: {e}", exc_info=True)
            raise DatabaseError(
                f"Agent lookup failed: {str(e)}",
                details={"extension": extension}
            )
    
    async def enrich_call_record(
        self, 
        call_data: Dict[str, Any], 
        binotel_payload: Dict[str, Any]
    ) -> Optional[str]:
        """
        Main enrichment pipeline: create enriched call record in database
        
        This function:
        1. Looks up/creates customer
        2. Looks up agent
        3. Creates call record with all metadata
        4. Triggers analytics refresh
        
        Args:
            call_data: Parsed call data from webhook
            binotel_payload: Raw webhook payload for reference
            
        Returns:
            Internal call UUID or None if database unavailable
            
        Raises:
            DatabaseError: If critical database operations fail
        """
        if not self.supabase:
            logger.warning("Supabase not configured, skipping enrichment")
            return None
        
        try:
            phone = call_data.get("phone", "unknown")
            extension = call_data.get("extension", "")
            
            logger.info(
                f"Starting enrichment for call {call_data.get('uuid')}",
                extra={"call_id": call_data.get('uuid')}
            )
            
            # Run customer and agent lookups in parallel for efficiency
            customer_id, agent_id = await asyncio.gather(
                self.get_or_create_customer(phone),
                self.get_agent_id(extension),
                return_exceptions=False  # Let exceptions propagate
            )
            
            # Prepare enriched call record
            call_record = {
                "binotel_uuid": call_data.get("uuid"),
                "direction": call_data.get("direction", "incoming"),
                "status": call_data.get("status", "completed"),
                "phone_number": phone,
                "agent_extension": extension,
                "agent_id": agent_id,
                "customer_id": customer_id,
                "duration_seconds": call_data.get("duration", 0),
                "recording_url": call_data.get("recording_url"),
                "started_at": datetime.utcnow().isoformat(),
                "raw_payload": binotel_payload  # Store for debugging
            }
            
            # Upsert to handle duplicates (Binotel sometimes sends same event twice)
            logger.info("Saving enriched call record to database")
            
            response = self.supabase.table("calls") \
                .upsert(call_record, on_conflict="binotel_uuid") \
                .execute()
            
            if not response.data:
                raise DatabaseError("Call record save returned no data")
            
            internal_uuid = response.data[0]["id"]
            
            logger.info(
                f"Successfully saved enriched call record: {internal_uuid}",
                extra={"call_id": call_data.get('uuid'), "internal_uuid": internal_uuid}
            )
            
            # Trigger analytics refresh asynchronously (don't wait for it)
            try:
                self.supabase.rpc(
                    "refresh_analytics_agent_daily",
                    {"p_days_back": 1}
                ).execute()
                logger.info("Triggered analytics refresh")
            except Exception as analytics_error:
                # Non-critical, just log and continue
                logger.warning(f"Analytics refresh failed: {analytics_error}")
            
            return internal_uuid
            
        except Exception as e:
            logger.error(
                f"Enrichment pipeline failed for call {call_data.get('uuid')}: {e}",
                extra={"call_id": call_data.get('uuid')},
                exc_info=True
            )
            raise DatabaseError(
                f"Enrichment failed: {str(e)}",
                details={"call_id": call_data.get('uuid')}
            )


# Global service instance
enrichment_service = EnrichmentService()
