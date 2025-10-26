#!/bin/bash

# ============================================================================
# Script: 04_grant_permissions.sh
# Purpose: Grant IAM permissions to service accounts
# Time: ~2 minutes
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 4: Grant IAM Permissions"
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
TOOL_EXECUTOR_EMAIL="${TOOL_EXECUTOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${YELLOW}🔐 Granting permissions (using least-privilege principle)...${NC}"
echo ""

# ============================================================================
# ORCHESTRATOR PERMISSIONS
# ============================================================================
echo -e "${YELLOW}Configuring: $ORCHESTRATOR_SA${NC}"

# Vertex AI - to call Gemini LLM
echo "  • Vertex AI User"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/aiplatform.user" \
    --condition=None \
    > /dev/null 2>&1

# Firestore - to read/write user sessions and state
echo "  • Firestore User"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/datastore.user" \
    --condition=None \
    > /dev/null 2>&1

# Secret Manager - to read API keys and JWT secrets
echo "  • Secret Manager Accessor"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None \
    > /dev/null 2>&1

# DLP - to detect and redact PII
echo "  • DLP User"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/dlp.user" \
    --condition=None \
    > /dev/null 2>&1

# Cloud Logging - to write audit logs
echo "  • Log Writer"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/logging.logWriter" \
    --condition=None \
    > /dev/null 2>&1

# Cloud Run Invoker - to call tool services
echo "  • Cloud Run Invoker"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${ORCHESTRATOR_EMAIL}" \
    --role="roles/run.invoker" \
    --condition=None \
    > /dev/null 2>&1

echo -e "${GREEN}✅ Orchestrator permissions granted${NC}"

# ============================================================================
# TOOL EXECUTOR PERMISSIONS
# ============================================================================
echo ""
echo -e "${YELLOW}Configuring: $TOOL_EXECUTOR_SA${NC}"

# Firestore - limited read/write for tool results
echo "  • Firestore User"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${TOOL_EXECUTOR_EMAIL}" \
    --role="roles/datastore.user" \
    --condition=None \
    > /dev/null 2>&1

# Cloud Logging - to write tool execution logs
echo "  • Log Writer"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${TOOL_EXECUTOR_EMAIL}" \
    --role="roles/logging.logWriter" \
    --condition=None \
    > /dev/null 2>&1

echo -e "${GREEN}✅ Tool executor permissions granted${NC}"

# ============================================================================
# VERIFICATION
# ============================================================================
echo ""
echo -e "${YELLOW}🔍 Verifying permissions...${NC}"
echo ""
echo "Orchestrator ($ORCHESTRATOR_SA) has:"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:${ORCHESTRATOR_EMAIL}" \
    --format="table(bindings.role)" | grep -v "ROLE" | sed 's/^/  • /'

echo ""
echo "Tool Executor ($TOOL_EXECUTOR_SA) has:"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:${TOOL_EXECUTOR_EMAIL}" \
    --format="table(bindings.role)" | grep -v "ROLE" | sed 's/^/  • /'

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 4 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "IAM Roles Summary:"
echo "  Orchestrator: 6 roles (AI, DB, Secrets, DLP, Logging, Invoke)"
echo "  Tool Executor: 2 roles (DB, Logging)"
echo ""
echo "Next: Run ./05_setup_firestore.sh"
