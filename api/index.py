"""
Vercel Serverless Entry Point for Connecter Middleware
Handles all routing for FastAPI application in Vercel environment
"""

import sys
import os

# Add the project root directory to sys.path
# This is necessary because 'api/index.py' is running inside the 'api' folder,
# but we need to import modules from the 'backend' folder in the root.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import FastAPI app directly
from backend.src.api.main import app

# Set root_path to /api for Vercel deployment
# This ensures that requests to /api/endpoint are correctly routed to /endpoint in FastAPI
app.root_path = "/api"
