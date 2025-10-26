#!/bin/bash

# ============================================================================
# Script: 03_create_service_accounts.sh
# Purpose: Create service accounts for orchestrator and tools
# Time: ~1 minute
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 3: Create Service Accounts"
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

echo -e "${YELLOW}🔧 Creating service accounts...${NC}"
echo ""

# Create Orchestrator Service Account
echo "Creating: $ORCHESTRATOR_SA"
if gcloud iam service-accounts describe "${ORCHESTRATOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com" &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  Service account already exists, skipping...${NC}"
else
    gcloud iam service-accounts create $ORCHESTRATOR_SA \
        --display-name="Orchestrator Service Account" \
        --description="Main AI orchestrator service that manages conversation flow, LLM calls, and tool routing"
    echo -e "${GREEN}  ✅ Created ${ORCHESTRATOR_SA}${NC}"
fi

# Create Tool Executor Service Account
echo ""
echo "Creating: $TOOL_EXECUTOR_SA"
if gcloud iam service-accounts describe "${TOOL_EXECUTOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com" &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  Service account already exists, skipping...${NC}"
else
    gcloud iam service-accounts create $TOOL_EXECUTOR_SA \
        --display-name="Tool Executor Service Account" \
        --description="Executes external tool calls and API integrations with limited permissions"
    echo -e "${GREEN}  ✅ Created ${TOOL_EXECUTOR_SA}${NC}"
fi

echo ""
echo -e "${YELLOW}🔍 Verifying service accounts...${NC}"
gcloud iam service-accounts list --filter="email:*-sa@"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 3 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service accounts created:"
echo "  • ${ORCHESTRATOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "  • ${TOOL_EXECUTOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "Next: Run ./04_grant_permissions.sh"
