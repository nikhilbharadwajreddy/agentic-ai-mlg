#!/bin/bash

# ============================================================================
# Script: 02_enable_apis.sh
# Purpose: Enable all required GCP APIs
# Time: ~2 minutes
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 2: Enable GCP APIs"
echo "============================================"

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}❌ Error: .env file not found${NC}"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

echo -e "${YELLOW}📦 Enabling APIs (this takes ~2 minutes)...${NC}"
echo ""

# List of APIs to enable
APIS=(
    "run.googleapis.com"                    # Cloud Run
    "firestore.googleapis.com"              # Firestore Database
    "secretmanager.googleapis.com"          # Secret Manager
    "aiplatform.googleapis.com"             # Vertex AI
    "dlp.googleapis.com"                    # Data Loss Prevention
    "logging.googleapis.com"                # Cloud Logging
    "cloudscheduler.googleapis.com"         # Cloud Scheduler
    "pubsub.googleapis.com"                 # Pub/Sub
    "cloudbuild.googleapis.com"             # Cloud Build
    "artifactregistry.googleapis.com"       # Artifact Registry
    "compute.googleapis.com"                # Compute (required for VPC)
    "vpcaccess.googleapis.com"              # VPC Access
)

# Enable all APIs at once (faster than one-by-one)
echo "Enabling ${#APIS[@]} APIs..."
gcloud services enable "${APIS[@]}" --project=$PROJECT_ID

echo ""
echo -e "${GREEN}✅ All APIs enabled successfully!${NC}"
echo ""

# Verify enabled APIs
echo -e "${YELLOW}🔍 Verifying enabled APIs...${NC}"
ENABLED_COUNT=0
for api in "${APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "  ✓ $api"
        ((ENABLED_COUNT++))
    else
        echo "  ✗ $api (NOT ENABLED)"
    fi
done

echo ""
if [ $ENABLED_COUNT -eq ${#APIS[@]} ]; then
    echo -e "${GREEN}✅ All $ENABLED_COUNT APIs verified!${NC}"
else
    echo -e "${YELLOW}⚠️  Only $ENABLED_COUNT/${#APIS[@]} APIs verified${NC}"
    echo "Some APIs might still be enabling. Wait 30 seconds and run verify_setup.sh"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 2 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Next: Run ./03_create_service_accounts.sh"
