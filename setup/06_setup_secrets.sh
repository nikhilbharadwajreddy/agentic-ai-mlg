#!/bin/bash

# ============================================================================
# Script: 06_setup_secrets.sh
# Purpose: Initialize Secret Manager with placeholder secrets
# Time: ~1 minute
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 6: Setup Secret Manager"
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

ORCHESTRATOR_EMAIL="${ORCHESTRATOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${YELLOW}🔐 Creating secrets...${NC}"
echo ""

# ============================================================================
# Create JWT Secret
# ============================================================================
echo "Creating: jwt-secret"
if gcloud secrets describe jwt-secret &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  Secret already exists, skipping...${NC}"
else
    # Generate a secure random JWT secret
    JWT_SECRET=$(openssl rand -base64 32)
    echo -n "$JWT_SECRET" | gcloud secrets create jwt-secret \
        --data-file=- \
        --replication-policy="automatic"
    
    echo -e "${GREEN}  ✅ Created jwt-secret${NC}"
fi

# Grant access to orchestrator
gcloud secrets add-iam-policy-binding jwt-secret \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    > /dev/null 2>&1

# ============================================================================
# Create OTP API Key (placeholder)
# ============================================================================
echo ""
echo "Creating: otp-api-key"
if gcloud secrets describe otp-api-key &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  Secret already exists, skipping...${NC}"
else
    echo -n "PLACEHOLDER_UPDATE_LATER" | gcloud secrets create otp-api-key \
        --data-file=- \
        --replication-policy="automatic"
    
    echo -e "${GREEN}  ✅ Created otp-api-key (placeholder)${NC}"
fi

# Grant access to orchestrator
gcloud secrets add-iam-policy-binding otp-api-key \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    > /dev/null 2>&1

# ============================================================================
# Create additional secrets (placeholders for future use)
# ============================================================================
echo ""
echo "Creating: vertex-ai-config (optional)"
if gcloud secrets describe vertex-ai-config &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  Secret already exists, skipping...${NC}"
else
    echo -n '{"model":"gemini-1.5-pro","temperature":0.7}' | gcloud secrets create vertex-ai-config \
        --data-file=- \
        --replication-policy="automatic"
    
    echo -e "${GREEN}  ✅ Created vertex-ai-config${NC}"
fi

# Grant access to orchestrator
gcloud secrets add-iam-policy-binding vertex-ai-config \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    > /dev/null 2>&1

# ============================================================================
# Verification
# ============================================================================
echo ""
echo -e "${YELLOW}🔍 Verifying secrets...${NC}"
echo ""
gcloud secrets list --format="table(name,createTime,replication.automatic)"

echo ""
echo -e "${YELLOW}📝 How to update secrets later:${NC}"
echo ""
echo "Update jwt-secret:"
echo "  echo -n 'your-new-secret' | gcloud secrets versions add jwt-secret --data-file=-"
echo ""
echo "Update otp-api-key (e.g., Twilio):"
echo "  echo -n 'your-twilio-key' | gcloud secrets versions add otp-api-key --data-file=-"
echo ""
echo "View secret value (for debugging):"
echo "  gcloud secrets versions access latest --secret=jwt-secret"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 6 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Secrets created:"
echo "  • jwt-secret (auto-generated, secure)"
echo "  • otp-api-key (placeholder - update later)"
echo "  • vertex-ai-config (default model config)"
echo ""
echo "Secret Manager Console: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo ""
echo "Next: Run ./07_setup_artifact_registry.sh"
