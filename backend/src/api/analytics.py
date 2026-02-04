from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import date, timedelta
from src.services.agent_metrics import metrics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard/realtime")
async def get_realtime_dashboard():
    """Get live metrics for the main dashboard"""
    return await metrics_service.get_realtime_metrics()

@router.get("/leaderboard")
async def get_leaderboard(metric: str = "total_calls", limit: int = 10):
    """Get agent leaderboard for today"""
    return await metrics_service.get_leaderboard(metric, limit)

@router.get("/agent/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str, 
    start_date: Optional[date] = None, 
    end_date: Optional[date] = None
):
    """Get statistics for a specific agent"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
        
    return await metrics_service.get_agent_stats(agent_id, start_date, end_date)

@router.get("/customer/{phone}/history")
async def get_customer_history(phone: str):
    """Get recent call history for a customer"""
    return await metrics_service.get_customer_history(phone)
