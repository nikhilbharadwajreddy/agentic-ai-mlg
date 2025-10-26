# AI Agent Orchestrator

Production-ready AI agent with strict workflow enforcement, PII protection, and tool calling capabilities.

## Architecture

### Core Components

1. **State Machine**: Enforces workflow steps (terms → name → email → phone → OTP → active)
2. **Security Manager**: Handles JWT auth and PII redaction via Cloud DLP
3. **LLM Client**: Vertex AI integration with function calling
4. **Tool Registry**: Allowlist-based tool execution with schema validation

### Security Features

- Stateless JWT authentication
- Cloud DLP for PII detection and redaction
- No PII sent to LLM or logged
- Allowlist-based tool execution
- Step-by-step workflow enforcement (no skipping)
- Audit logging to Cloud Logging

## Prerequisites

- GCP Project with billing enabled
- APIs enabled (Run, Firestore, Secret Manager, Vertex AI, DLP)
- Service accounts created (orchestrator-sa, tool-executor-sa)
- Artifact Registry repository created

## Local Development

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your project ID
nano .env
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Authenticate with GCP

```bash
gcloud auth application-default login
```

### 4. Run Locally

```bash
python -m orchestrator.main
```

Server runs at: http://localhost:8080

## Testing the API

### Health Check

```bash
curl http://localhost:8080/health
```

### Chat Endpoint

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "message": "Hello, I accept the terms"
  }'
```

### Get User State

```bash
curl http://localhost:8080/api/v1/state/test_user_123
```

### List Available Tools

```bash
curl -X POST http://localhost:8080/api/v1/tools/list
```

## Deployment to Cloud Run

### Option 1: Using Cloud Build (Recommended)

```bash
gcloud builds submit --config cloudbuild.yaml
```

### Option 2: Manual Deployment

```bash
# Build image
docker build -t us-central1-docker.pkg.dev/agentic-ai-mlg/agentic-ai-mlg/orchestrator:latest .

# Push to registry
docker push us-central1-docker.pkg.dev/agentic-ai-mlg/agentic-ai-mlg/orchestrator:latest

# Deploy to Cloud Run
gcloud run deploy orchestrator-service \
  --image us-central1-docker.pkg.dev/agentic-ai-mlg/agentic-ai-mlg/orchestrator:latest \
  --region us-central1 \
  --platform managed \
  --service-account orchestrator-sa@agentic-ai-mlg.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=agentic-ai-mlg \
  --allow-unauthenticated
```

## Workflow Steps

1. **AWAITING_TERMS**: User must accept terms and conditions
2. **AWAITING_NAME**: Collect user's name
3. **AWAITING_EMAIL**: Collect and validate email
4. **AWAITING_PHONE**: Collect phone number
5. **AWAITING_OTP**: Verify OTP (demo code: 123456)
6. **ACTIVE**: Full access with tool calling enabled

Users CANNOT skip steps. The state machine enforces strict progression.

## Available Tools

### 1. schedule_appointment
Schedule an appointment for the user.

Parameters:
- date (string, required): YYYY-MM-DD format
- time (string, required): HH:MM format (24-hour)
- purpose (string, required): Purpose of appointment
- duration_minutes (integer, optional): Duration in minutes (default: 30)

### 2. get_available_slots
Get available appointment slots for a date.

Parameters:
- date (string, required): YYYY-MM-DD format

### 3. cancel_appointment
Cancel an existing appointment.

Parameters:
- appointment_id (string, required): ID of appointment to cancel

## Security Best Practices

1. **Secrets**: Always use Secret Manager, never hardcode
2. **PII**: Redact before sending to LLM or logging
3. **Auth**: Verify JWT on sensitive endpoints
4. **Tools**: Allowlist only, validate schemas
5. **Logging**: Mask sensitive fields
6. **Network**: Use private IPs where possible

## Monitoring

View logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-service" --limit 50 --format json
```

View metrics:
- Cloud Run dashboard: https://console.cloud.google.com/run

## Troubleshooting

### "Permission denied" errors
- Verify service account has required IAM roles
- Check VPC Service Controls if enabled

### "Secret not found"
- Update Secret Manager values from placeholders
- Grant service account access to secrets

### DLP errors
- Ensure DLP API is enabled
- Check project quota for DLP requests

## Project Structure

```
orchestrator/
├── main.py              # FastAPI application
├── state_machine.py     # Workflow engine
├── llm_client.py        # Vertex AI wrapper
├── security.py          # Auth + PII handling
├── models.py            # Data models
└── tools/
    └── registry.py      # Tool definitions
```

## License

Internal use only.
