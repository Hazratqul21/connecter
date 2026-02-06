"""
Vercel Serverless Entry Point for Connecter Middleware
Handles all routing for FastAPI application in Vercel environment
"""

# Import FastAPI app directly
from backend.src.api.main import app

# Set root_path to /api for Vercel deployment
# This ensures that requests to /api/endpoint are correctly routed to /endpoint in FastAPI
app.root_path = "/api"
