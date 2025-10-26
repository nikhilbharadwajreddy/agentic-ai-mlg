# DEPLOYMENT GUIDE

Complete step-by-step guide to deploy the AI Agent Orchestrator to Cloud Run.

## Prerequisites Completed
- GCP Project: agentic-ai-mlg
- APIs enabled
- Service accounts created
- Firestore initialized
- Secret Manager configured
- Artifact Registry created

## Step 1: Test Locally First

### 1.1 Create Virtual Environment
```bash
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg
python3 -m venv venv
source venv/bin/activate
```

### 1.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.3 Set Environment Variable
```bash
export GCP_PROJECT_ID=agentic-ai-mlg
```

### 1.4 Authenticate with GCP
```bash
gcloud auth application-default login
```

### 1.5 Run the Server
```bash
python -m orchestrator.main
```

Server should start at: http://localhost:8080

### 1.6 Test in Another Terminal
```bash
# Open new terminal
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg
source venv/bin/activate
python tests/test_local.py
```

If tests pass, proceed to deployment.

## Step 2: Update Secrets

Before deploying, update the placeholder secrets with real values.

### 2.1 Update JWT Secret
```bash
# Generate a secure random secret
openssl rand -base64 32

# Update the secret
echo "YOUR_GENERATED_SECRET" | gcloud secrets versions add jwt-secret --data-file=-
```

### 2.2 OTP API Key (if using real SMS service)
```bash
# If using Twilio, Vonage, etc.
echo "YOUR_API_KEY" | gcloud secrets versions add otp-api-key --data-file=-
```

## Step 3: Build and Push Docker Image

### 3.1 Authenticate Docker
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 3.2 Build Image
```bash
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg

docker build -t us-central1-docker.pkg.dev/agentic-ai-mlg/agentic-ai-mlg/orchestrator:v1 .
```

### 3.3 Push to Artifact Registry
```bash
docker push us-central1-docker.pkg.dev/agentic-ai-mlg/agentic-ai-mlg/orchestrator:v1
```

## Step 4: Deploy to Cloud Run

### 4.1 Deploy Service
```bash
gcloud run deploy orchestrator-service \
  --image us-central1-docker.pkg.dev/agentic-ai-mlg/agentic-ai-mlg/orchestrator:v1 \
  --region us-central1 \
  --platform managed \
  --service-account orchestrator-sa@agentic-ai-mlg.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT_ID=agentic-ai-mlg,GCP_REGION=us-central1,ENVIRONMENT=production \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
```

### 4.2 Get Service URL
```bash
gcloud run services describe orchestrator-service \
  --region us-central1 \
  --format 'value(status.url)'
```

Copy the URL (e.g., https://orchestrator-service-xxxxx-uc.a.run.app)

## Step 5: Test Production Deployment

### 5.1 Health Check
```bash
curl https://YOUR-SERVICE-URL/health
```

Should return: {"status":"healthy","service":"orchestrator"}

### 5.2 Test Chat
```bash
curl -X POST https://YOUR-SERVICE-URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "prod_test_user",
    "message": "I accept the terms"
  }'
```

### 5.3 Test Complete Workflow
Create a test script:

```bash
# Save as test_production.sh
SERVICE_URL="YOUR-SERVICE-URL"
USER_ID="demo_user_$(date +%s)"

echo "Testing Terms..."
curl -X POST $SERVICE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"message\":\"I accept the terms\"}"

echo "\n\nTesting Name..."
curl -X POST $SERVICE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"message\":\"My name is Jane Doe\"}"

echo "\n\nTesting Email..."
curl -X POST $SERVICE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"message\":\"jane@example.com\"}"

echo "\n\nTesting Phone..."
curl -X POST $SERVICE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"message\":\"555-0123\"}"

echo "\n\nTesting OTP..."
curl -X POST $SERVICE_URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"message\":\"123456\"}"
```

## Step 6: Monitor and Debug

### 6.1 View Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-service" \
  --limit 50 \
  --format json
```

### 6.2 View Metrics
Go to: https://console.cloud.google.com/run/detail/us-central1/orchestrator-service

### 6.3 Check Firestore
Go to: https://console.cloud.google.com/firestore
Look for "user_states" collection

## Step 7: Automated Deployment (Optional)

For future deployments, use Cloud Build:

```bash
gcloud builds submit --config cloudbuild.yaml
```

This automatically:
1. Builds Docker image
2. Pushes to Artifact Registry
3. Deploys to Cloud Run

## Troubleshooting

### Error: "Permission Denied"
```bash
# Grant missing permissions
gcloud projects add-iam-policy-binding agentic-ai-mlg \
  --member="serviceAccount:orchestrator-sa@agentic-ai-mlg.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Error: "Secret not found"
```bash
# Verify secret exists
gcloud secrets list

# Update secret value
echo "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Error: "Firestore not initialized"
```bash
gcloud firestore databases create --location=us-central1 --type=firestore-native
```

### Error: "DLP quota exceeded"
- Check quotas: https://console.cloud.google.com/iam-admin/quotas
- Request increase if needed

## Production Checklist

Before going live:

- [ ] Update JWT secret with strong random value
- [ ] Configure real OTP service (Twilio, etc.)
- [ ] Set up monitoring alerts
- [ ] Configure custom domain (optional)
- [ ] Enable Cloud Armor for WAF (optional)
- [ ] Set up CI/CD pipeline
- [ ] Document frontend integration
- [ ] Perform load testing
- [ ] Create backup/disaster recovery plan

## Frontend Integration

Your frontend should:

1. Call `/api/v1/chat` endpoint with user_id and message
2. Display response.response to user
3. Track current_step to show progress
4. Handle requires_action field (e.g., show OTP input)

Example frontend code:
```javascript
async function sendMessage(userId, message) {
  const response = await fetch('https://YOUR-SERVICE-URL/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message })
  });
  
  const data = await response.json();
  return data;
}
```

## Next Steps

1. Test locally
2. Deploy to Cloud Run
3. Test production deployment
4. Integrate with frontend
5. Add more tools as needed
6. Monitor and iterate
