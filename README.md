# Connecter Middleware v2.0

Professional middleware solution connecting Binotel telephony system with HelpDeskEddy CRM, enhanced with AI-powered call intelligence.

## Overview

Connecter Middleware acts as a bridge between your telephony system (Binotel) and your CRM (HelpDeskEddy), while providing additional AI-powered insights through automatic call transcription and analysis.

### Key Features

- **Real-time Call Integration**: Automatically forwards call data from Binotel to HelpDeskEddy
- **AI-Powered Transcription**: Uses OpenAI Whisper to transcribe call recordings
- **Intelligent Analysis**: GPT-4o-mini analyzes transcripts for sentiment, topics, and action items
- **Customer Enrichment**: Automatic customer profile creation and lookup
- **Agent Metrics**: Real-time analytics on agent performance
- **Robust Error Handling**: Fault-tolerant processing with comprehensive logging
- **Production Ready**: Optimized for Vercel serverless deployment

## Architecture

The middleware follows a three-stage processing pipeline:

1. **Webhook Reception**: Receives and validates incoming Binotel events
2. **CRM Sync**: Forwards call data to HelpDeskEddy (synchronous)
3. **Background Processing**: 
   - Database enrichment (customer/agent lookup)
   - AI transcription and analysis
   - Analytics refresh

### Technology Stack

- **Framework**: FastAPI (Python)
- **AI**: OpenAI (Whisper + GPT-4o-mini)
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Vercel Serverless
- **Frontend**: Next.js (React)

## Project Structure

```
connecter/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI application entry point
│   ├── core/
│   │   ├── config.py            # Configuration and settings
│   │   ├── database.py          # Database connection
│   │   ├── logging_config.py    # Logging setup
│   │   ├── exceptions.py        # Custom exception classes
│   │   └── webhook_parser.py    # Webhook validation
│   └── services/
│       ├── orchestrator.py      # Main processing coordinator
│       ├── helpdesk_service.py  # HelpDeskEddy integration
│       ├── enrichment_service.py # Database enrichment
│       └── ai_service.py        # AI transcription & analysis
├── frontend/                    # Next.js dashboard (optional)
├── requirements.txt             # Python dependencies
└── vercel.json                 # Vercel deployment config
```

## Configuration

All credentials are hardcoded in `src/core/config.py` for production stability:

- **Binotel API**: Credentials for telephony system access
- **HelpDeskEddy**: CRM webhook endpoint
- **OpenAI**: API key for AI processing
- **Supabase**: Database connection (via environment variables)

### Environment Variables (Supabase only)

Set these in your Vercel project settings:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Deployment

### Vercel Deployment

1. **Connect Repository**: Link your GitHub repository to Vercel

2. **Set Environment Variables**:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

3. **Deploy**: Vercel will automatically detect the configuration

The deployment configuration in `vercel.json` handles both the Python backend and Next.js frontend.

### Local Development

1. **Install Dependencies**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set Environment Variables**:
```bash
export SUPABASE_URL=your_url
export SUPABASE_KEY=your_key
```

3. **Run Server**:
```bash
python -m uvicorn src.api.main:app --reload
```

4. **Access API**:
   - Main: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## API Endpoints

### Main Endpoints

- **POST /webhook**: Receives Binotel call events
- **GET /**: System status dashboard (HTML)
- **GET /health**: Health check for monitoring
- **GET /stats**: Processing statistics
- **GET /docs**: Interactive API documentation

### Webhook Payload Example

Binotel sends POST requests with the following structure:

```json
{
  "generalCallID": "123456789",
  "requestType": "callCompleted",
  "direction": "incoming",
  "status": "ANSWER",
  "externalNumber": "+998901234567",
  "internalNumber": "101",
  "billsec": 180,
  "recordingUrl": "https://..."
}
```

## Features Explained

### 1. Webhook Processing

The middleware validates incoming webhooks and only processes these event types:
- `apiCallCompleted`
- `callCompleted`
- `incomingCallCompleted`
- `outgoingCallCompleted`

All other events are logged but ignored.

### 2. HelpDeskEddy Integration

Call data is immediately forwarded to HelpDeskEddy with retry logic (up to 3 attempts with exponential backoff). This happens synchronously before the webhook response is returned.

### 3. Database Enrichment

The system maintains a structured database of:
- **Customers**: Automatically created on first call
- **Agents**: Linked by extension number
- **Calls**: Complete call history with metadata
- **Enrichments**: AI-generated insights

### 4. AI Processing

For calls with recordings:
1. Audio is downloaded and validated (max 25MB)
2. Whisper transcribes the audio
3. GPT-4o-mini analyzes the transcript for:
   - Summary
   - Sentiment score (1-10)
   - Detected topics/tags
   - Action items
   - Urgency level

### 5. Error Handling

The system is designed to be fault-tolerant:
- HelpDeskEddy errors don't prevent database saves
- Database errors prevent AI processing (dependency)
- AI errors are logged but don't fail the webhook
- All errors are structured and logged with context

## Monitoring

### Built-in Dashboard

Visit the root URL (/) to see:
- System status
- Processing statistics
- Last webhook information
- Uptime and health

### Logs

All operations are logged with structured JSON format including:
- Timestamp (UTC)
- Log level
- Module and function
- Message
- Call ID (when applicable)
- Exception traces

### Health Check

Use `/health` endpoint for uptime monitoring:

```bash
curl https://your-domain.vercel.app/health
```

## Security Considerations

1. **Credentials**: All API credentials are hardcoded in source (not recommended for sensitive production, but acceptable for this use case)

2. **CORS**: Currently allows all origins - restrict in production

3. **Rate Limiting**: Consider adding rate limiting for the webhook endpoint

4. **Authentication**: No authentication on webhook endpoint - Binotel sends unsigned requests

## Troubleshooting

### Common Issues

**Webhook not processing**:
- Check event type is in valid list
- Verify `generalCallID` is present
- Review logs at `/stats`

**HelpDeskEddy errors**:
- Verify webhook URL is correct
- Check network connectivity
- Review retry attempts in logs

**AI processing fails**:
- Verify OpenAI API key is valid
- Check audio file is accessible
- Ensure audio size is under 25MB

**Database errors**:
- Confirm Supabase environment variables
- Check database connection
- Verify table schemas exist

## Database Schema

Required Supabase tables:

```sql
-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    tags TEXT[],
    created_via VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extension_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Calls table
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    binotel_uuid VARCHAR(255) UNIQUE NOT NULL,
    direction VARCHAR(20),
    status VARCHAR(50),
    phone_number VARCHAR(50),
    agent_extension VARCHAR(20),
    agent_id UUID REFERENCES agents(id),
    customer_id UUID REFERENCES customers(id),
    duration_seconds INTEGER,
    recording_url TEXT,
    started_at TIMESTAMP,
    raw_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Call enrichments table
CREATE TABLE call_enrichments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES calls(id) UNIQUE,
    transcription_text TEXT,
    summary TEXT,
    sentiment_score INTEGER,
    detected_topics TEXT[],
    action_items TEXT[],
    urgency_score INTEGER,
    key_points TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Webhook logs table (debugging)
CREATE TABLE webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payload JSONB,
    request_type VARCHAR(100),
    call_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Performance

### Optimization Features

- **Connection Pooling**: Reuses OpenAI and database connections
- **Parallel Processing**: Customer and agent lookups run concurrently
- **Background Tasks**: AI processing doesn't block webhook response
- **Efficient Logging**: Structured JSON logs for easy parsing
- **Smart Caching**: Configuration loaded once and cached

### Resource Usage

- **Memory**: ~100MB base + ~50MB per concurrent AI job
- **CPU**: Minimal (most work is I/O bound)
- **Bandwidth**: ~5-10MB per call (recording download)

## Future Enhancements

Potential improvements for future versions:

1. **Real-time notifications**: WebSocket support for live call updates
2. **Advanced analytics**: Custom dashboards with Grafana
3. **Multi-language**: Support for Uzbek/Russian transcription
4. **Call quality**: Automatic quality scoring
5. **Integration expansion**: Additional CRM systems
6. **Webhook signatures**: Secure webhook validation
7. **Rate limiting**: Protect against abuse
8. **Caching layer**: Redis for frequently accessed data

## Support

For issues or questions:

1. Check the `/stats` endpoint for processing statistics
2. Review structured logs for error details
3. Verify all configuration in `src/core/config.py`
4. Test webhooks using the `/docs` interface

## License

This project is proprietary software developed for internal use.

## Version History

### v2.0.0 (Current)
- Complete architectural refactor
- Professional error handling and logging
- Improved fault tolerance
- Enhanced monitoring and statistics
- Structured service architecture
- Comprehensive documentation

### v1.0.0
- Initial implementation
- Basic webhook processing
- Simple HelpDeskEddy forwarding
