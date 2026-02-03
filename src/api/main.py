"""
Connecter Middleware - Main API Application
Professional middleware connecting Binotel telephony with HelpDeskEddy CRM
Includes AI-powered call intelligence and comprehensive logging
"""
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
import sys

# Core imports
from src.core.config import settings
from src.core.logging_config import setup_logging, get_logger
from src.core.database import initialize_supabase
from src.core.webhook_parser import parse_binotel_webhook, validate_webhook_event
from src.core.exceptions import (
    ConnecterException,
    WebhookValidationError,
    HelpDeskEddyError,
    AIProcessingError,
    DatabaseError
)

# Service imports
from src.services.orchestrator import orchestrate_call_processing

# Initialize logging first
setup_logging(debug_mode=settings.DEBUG_MODE)
logger = get_logger(__name__)

# Initialize Supabase connection
initialize_supabase()

# Configure timezone
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional middleware for Binotel-HelpDeskEddy integration",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for monitoring
webhook_stats = {
    "total_received": 0,
    "total_processed": 0,
    "total_ignored": 0,
    "total_errors": 0,
    "last_webhook_time": None,
    "last_webhook_payload": None
}


@app.on_event("startup")
async def startup_event():
    """Application startup event - log initialization"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting up")
    logger.info(f"Debug mode: {settings.DEBUG_MODE}")
    logger.info(f"Environment: Vercel Serverless")
    

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event - cleanup"""
    logger.info(f"👋 {settings.APP_NAME} shutting down")


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Root endpoint - System status dashboard
    Returns HTML page with current system status and statistics
    """
    current_time = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare last webhook info
    last_webhook_info = "No webhooks received yet"
    if webhook_stats["last_webhook_time"]:
        last_webhook_info = f"""
        <strong>Last received:</strong> {webhook_stats['last_webhook_time']}<br>
        <strong>Call ID:</strong> {webhook_stats.get('last_call_id', 'N/A')}<br>
        <strong>Status:</strong> {webhook_stats.get('last_status', 'N/A')}
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 15px;
                background: #27ae60;
                color: white;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: #ecf0f1;
                padding: 20px;
                border-radius: 6px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stat-label {{
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 5px;
            }}
            .info-section {{
                background: #ecf0f1;
                padding: 20px;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                color: #95a5a6;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{settings.APP_NAME}</h1>
            <div>
                <span class="status-badge">✓ OPERATIONAL</span>
                <p><strong>Version:</strong> {settings.APP_VERSION}</p>
                <p><strong>Current Time:</strong> {current_time} (Tashkent)</p>
                <p><strong>Deployment:</strong> Vercel Serverless</p>
            </div>
            
            <h2>Statistics</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{webhook_stats['total_received']}</div>
                    <div class="stat-label">Total Webhooks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{webhook_stats['total_processed']}</div>
                    <div class="stat-label">Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{webhook_stats['total_ignored']}</div>
                    <div class="stat-label">Ignored</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{webhook_stats['total_errors']}</div>
                    <div class="stat-label">Errors</div>
                </div>
            </div>
            
            <div class="info-section">
                <h3>Last Webhook</h3>
                <p>{last_webhook_info}</p>
            </div>
            
            <div class="footer">
                <p>Connecter Middleware - Binotel ↔ HelpDeskEddy Integration</p>
                <p>Powered by FastAPI | Deployed on Vercel</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    Returns system health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(TASHKENT_TZ).isoformat()
    }


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for receiving Binotel call events
    
    Processing flow:
    1. Parse and validate webhook payload
    2. Log webhook to database (if configured)
    3. Send call to HelpDeskEddy (synchronous)
    4. Trigger background processing (database + AI)
    5. Return immediate success response
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        
    Returns:
        JSON response with processing status
    """
    request_id = f"req_{datetime.utcnow().timestamp()}"
    logger.info(f"📨 Webhook received", extra={"request_id": request_id})
    
    # Update stats
    webhook_stats["total_received"] += 1
    webhook_stats["last_webhook_time"] = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Step 1: Parse request payload
        content_type = request.headers.get("Content-Type", "")
        
        if "application/json" in content_type:
            raw_payload = await request.json()
        else:
            # Handle form-encoded data
            form_data = await request.form()
            raw_payload = dict(form_data)
        
        webhook_stats["last_webhook_payload"] = raw_payload
        
        # Step 2: Validate event type
        if not validate_webhook_event(raw_payload):
            webhook_stats["total_ignored"] += 1
            request_type = raw_payload.get("requestType", "unknown")
            logger.info(f"Ignoring event type: {request_type}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ignored",
                    "reason": f"Event type '{request_type}' not processed"
                }
            )
        
        # Step 3: Parse and validate payload structure
        try:
            parsed_call_data = parse_binotel_webhook(raw_payload)
        except WebhookValidationError as e:
            webhook_stats["total_errors"] += 1
            logger.error(f"Webhook validation failed: {e.message}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Invalid webhook payload",
                    "details": e.details
                }
            )
        
        # Update stats with call info
        webhook_stats["last_call_id"] = parsed_call_data.general_call_id
        webhook_stats["last_status"] = "processing"
        
        # Step 4: Log webhook to database (best effort)
        try:
            from src.core.database import get_supabase
            supabase = get_supabase()
            if supabase:
                supabase.table("webhook_logs").insert({
                    "payload": raw_payload,
                    "request_type": parsed_call_data.request_type,
                    "call_id": parsed_call_data.general_call_id
                }).execute()
        except Exception as log_error:
            # Non-critical, just log and continue
            logger.warning(f"Failed to log webhook: {log_error}")
        
        # Step 5: Prepare call data for processing
        call_summary_data = {
            "uuid": parsed_call_data.general_call_id,
            "direction": parsed_call_data.direction or "incoming",
            "status": parsed_call_data.status or "completed",
            "phone": parsed_call_data.phone_number,
            "extension": parsed_call_data.agent_extension,
            "duration": parsed_call_data.billsec,
            "recording_url": parsed_call_data.final_recording_url
        }
        
        # Step 6: Trigger background processing
        background_tasks.add_task(
            orchestrate_call_processing,
            call_summary_data=call_summary_data,
            binotel_payload=raw_payload
        )
        
        # Update stats
        webhook_stats["total_processed"] += 1
        webhook_stats["last_status"] = "success"
        
        logger.info(
            f"✓ Webhook accepted, background processing started",
            extra={"call_id": parsed_call_data.general_call_id}
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Call processing started",
                "call_id": parsed_call_data.general_call_id
            }
        )
    
    except ConnecterException as e:
        # Handle known application errors
        webhook_stats["total_errors"] += 1
        logger.error(f"Application error: {e.message}", exc_info=True)
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "message": e.message,
                "details": e.details
            }
        )
    
    except Exception as e:
        # Handle unexpected errors
        webhook_stats["total_errors"] += 1
        logger.error(f"Unexpected error in webhook handler: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "details": str(e) if settings.DEBUG_MODE else "Contact support"
            }
        )


@app.get("/stats")
async def get_stats():
    """
    Get webhook processing statistics
    Useful for monitoring and debugging
    """
    return {
        "statistics": webhook_stats,
        "timestamp": datetime.now(TASHKENT_TZ).isoformat()
    }


# Error handlers for better error responses
@app.exception_handler(ConnecterException)
async def connecter_exception_handler(request: Request, exc: ConnecterException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    # For local development
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
