#!/bin/bash

# ============================================================================
# Script: 08_configure_defaults.sh
# Purpose: Set default gcloud configurations
# Time: ~30 seconds
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 8: Configure Default Settings"
echo "============================================"

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}❌ Error: .env file not found${NC}"
    exit 1
fi

echo -e "${YELLOW}⚙️  Setting default configurations...${NC}"
echo ""

# Set default project
echo "Setting default project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Set default region for Cloud Run
echo "Setting default Cloud Run region: $REGION"
gcloud config set run/region $REGION

# Set default compute region
echo "Setting default compute region: $REGION"
gcloud config set compute/region $REGION

# Set default compute zone (first zone in region)
ZONE="${REGION}-a"
echo "Setting default compute zone: $ZONE"
gcloud config set compute/zone $ZONE

# Enable color output
gcloud config set core/disable_color False

echo ""
echo -e "${GREEN}✅ Defaults configured${NC}"

# Display current configuration
echo ""
echo -e "${YELLOW}🔍 Current gcloud configuration:${NC}"
echo ""
gcloud config list

# Create a summary file
echo ""
echo -e "${YELLOW}📄 Creating configuration summary...${NC}"

cat > ../config_summary.txt << EOF
# ================================================
# GCP Configuration Summary
# Generated: $(date)
# ================================================

PROJECT_ID: $PROJECT_ID
PROJECT_NAME: $PROJECT_NAME
REGION: $REGION
ZONE: $ZONE

# ================================================
# Service Accounts
# ================================================
Orchestrator: ${ORCHESTRATOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com
Tool Executor: ${TOOL_EXECUTOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com

# ================================================
# Resources
# ================================================
Firestore Database: (default)
  Location: $FIRESTORE_LOCATION
  Type: $FIRESTORE_TYPE

Artifact Registry: $REGISTRY_NAME
  Location: $REGISTRY_LOCATION
  URL: ${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}

# ================================================
# Secrets (Secret Manager)
# ================================================
- jwt-secret
- otp-api-key
- vertex-ai-config

# ================================================
# Useful Commands
# ================================================

# View Firestore data
gcloud firestore export gs://${PROJECT_ID}-backup

# View secrets
gcloud secrets versions access latest --secret=jwt-secret

# Deploy to Cloud Run
gcloud run deploy SERVICE_NAME \\
  --image ${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}/IMAGE:TAG \\
  --region $REGION \\
  --service-account ${ORCHESTRATOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# ================================================
# Console URLs
# ================================================
Cloud Console:
  https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID

Firestore:
  https://console.cloud.google.com/firestore/data?project=$PROJECT_ID

Secret Manager:
  https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID

Artifact Registry:
  https://console.cloud.google.com/artifacts?project=$PROJECT_ID

Cloud Run:
  https://console.cloud.google.com/run?project=$PROJECT_ID

Vertex AI:
  https://console.cloud.google.com/vertex-ai?project=$PROJECT_ID

IAM:
  https://console.cloud.google.com/iam-admin/iam?project=$PROJECT_ID

Logs:
  https://console.cloud.google.com/logs?project=$PROJECT_ID
EOF

echo -e "${GREEN}✅ Configuration saved to: ../config_summary.txt${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 8 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next: Run ./verify_setup.sh to validate everything!"
