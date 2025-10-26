#!/bin/bash

# ============================================================================
# Script: 01_create_project.sh
# Purpose: Create GCP project and set as default
# Time: ~2 minutes
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 1: Create GCP Project"
echo "============================================"

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.template to .env and configure it"
    echo "  cp .env.template .env"
    exit 1
fi

# Validate required variables
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: PROJECT_ID not set in .env${NC}"
    exit 1
fi

if [ -z "$PROJECT_NAME" ]; then
    echo -e "${RED}❌ Error: PROJECT_NAME not set in .env${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Project Name: $PROJECT_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI not found${NC}"
    echo "Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Authenticate if needed
echo -e "${YELLOW}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Please login to your Google Cloud account:"
    gcloud auth login
fi

# Check if project already exists
if gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${YELLOW}⚠️  Project $PROJECT_ID already exists${NC}"
    echo "Using existing project..."
else
    echo -e "${YELLOW}🚀 Creating project: $PROJECT_ID${NC}"
    
    # Create project
    if [ -z "$ORGANIZATION_ID" ]; then
        gcloud projects create $PROJECT_ID \
            --name="$PROJECT_NAME" \
            --set-as-default
    else
        gcloud projects create $PROJECT_ID \
            --name="$PROJECT_NAME" \
            --organization="$ORGANIZATION_ID" \
            --set-as-default
    fi
    
    echo -e "${GREEN}✅ Project created successfully${NC}"
fi

# Set as default project
echo -e "${YELLOW}🔧 Setting as default project...${NC}"
gcloud config set project $PROJECT_ID

# Verify
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" = "$PROJECT_ID" ]; then
    echo -e "${GREEN}✅ Project configured: $CURRENT_PROJECT${NC}"
else
    echo -e "${RED}❌ Error: Failed to set project${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Link Billing Account${NC}"
echo "Before proceeding, you must link a billing account:"
echo "1. Go to: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
echo "2. Click 'LINK A BILLING ACCOUNT'"
echo "3. Select your billing account"
echo ""
echo "Press ENTER after linking billing account..."
read -r

# Verify billing is enabled
echo -e "${YELLOW}🔍 Verifying billing...${NC}"
if gcloud beta billing projects describe $PROJECT_ID &> /dev/null; then
    echo -e "${GREEN}✅ Billing account linked${NC}"
else
    echo -e "${RED}❌ Warning: Could not verify billing${NC}"
    echo "Please ensure billing is enabled before continuing"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 1 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Next: Run ./02_enable_apis.sh"
