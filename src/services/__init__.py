"""
Connecter Middleware - Services Module
Contains business logic for call processing, AI analysis, and CRM integration
"""
from .orchestrator import orchestrate_call_processing
from .ai_service import ai_service, process_call_intelligence
from .enrichment_service import enrichment_service
from .helpdesk_service import helpdesk_service

__all__ = [
    "orchestrate_call_processing",
    "ai_service",
    "process_call_intelligence",
    "enrichment_service",
    "helpdesk_service"
]
