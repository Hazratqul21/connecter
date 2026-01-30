import logging
from typing import Optional, List, Dict, Any
from src.core.database import get_supabase
from datetime import datetime, date

logger = logging.getLogger(__name__)

class AgentMetricsService:
    """
    Service to fetch analytics and performance metrics for the Dashboard.
    Wraps Supabase RPC functions for performance.
    """
    
    def __init__(self):
        self.supabase = get_supabase()

    async def get_realtime_metrics(self) -> Dict[str, Any]:
        """
        Get live dashboard metrics (calls today, active agents, etc)
        """
        if not self.supabase: return {}
        try:
            response = self.supabase.rpc("get_realtime_metrics").execute()
            if response.data:
                # RPC returns a list of 1 object usually
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching realtime metrics: {e}")
            return {}

    async def get_agent_stats(self, agent_id: str, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get comprehensive stats for a specific agent.
        """
        if not self.supabase: return {}
        try:
            params = {
                "p_agent_id": agent_id,
                "p_start_date": start_date.isoformat(),
                "p_end_date": end_date.isoformat()
            }
            response = self.supabase.rpc("get_agent_stats", params).execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching agent stats: {e}")
            return {}

    async def get_leaderboard(self, metric: str = "total_calls", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get agent leaderboard for today.
        Metrics: total_calls, completed_calls, avg_handle_time, csat_score
        """
        if not self.supabase: return []
        try:
            # Check valid metrics to prevent SQL injection (though RPC handles it safely)
            valid_metrics = ["total_calls", "completed_calls", "total_talk_time", "avg_duration"]
            if metric not in valid_metrics:
                metric = "total_calls"

            params = {
                "p_metric": metric,
                "p_date": date.today().isoformat(),
                "p_limit": limit
            }
            response = self.supabase.rpc("get_agent_leaderboard", params).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {e}")
            return []

    async def get_customer_history(self, phone: str) -> List[Dict[str, Any]]:
        """
        Get recent calls for a customer.
        """
        if not self.supabase: return []
        try:
            params = {"p_phone_number": phone}
            response = self.supabase.rpc("get_customer_history", params).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching customer history: {e}")
            return []

metrics_service = AgentMetricsService()
