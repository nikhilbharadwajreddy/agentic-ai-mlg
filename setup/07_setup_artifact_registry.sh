#!/bin/bash

# ============================================================================
# Script: 07_setup_artifact_registry.sh
# Purpose: Create Artifact Registry for Docker images
# Time: ~1 minute
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 7: Setup Artifact Registry"
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

echo -e "${YELLOW}📦 Creating Docker repository...${NC}"
echo ""
echo "Registry name: $REGISTRY_NAME"
echo "Location: $REGISTRY_LOCATION"
echo ""

# Check if repository already exists
if gcloud artifacts repositories describe $REGISTRY_NAME --location=$REGISTRY_LOCATION &> /dev/null; then
    echo -e "${YELLOW}⚠️  Repository already exists, skipping...${NC}"
else
    # Create repository
    gcloud artifacts repositories create $REGISTRY_NAME \
        --repository-format=docker \
        --location=$REGISTRY_LOCATION \
        --description="Docker images for AI Agent services"
    
    echo -e "${GREEN}✅ Artifact Registry repository created!${NC}"
fi

# Configure Docker authentication
echo ""
echo -e "${YELLOW}🔐 Configuring Docker authentication...${NC}"
gcloud auth configure-docker ${REGISTRY_LOCATION}-docker.pkg.dev --quiet

echo -e "${GREEN}✅ Docker authentication configured${NC}"

# Verify repository
echo ""
echo -e "${YELLOW}🔍 Verifying repository...${NC}"
gcloud artifacts repositories list --location=$REGISTRY_LOCATION

echo ""
echo -e "${YELLOW}📝 How to use this repository:${NC}"
echo ""
echo "1. Build your Docker image:"
echo "   docker build -t orchestrator:latest ."
echo ""
echo "2. Tag for Artifact Registry:"
echo "   docker tag orchestrator:latest \\"
echo "     ${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}/orchestrator:latest"
echo ""
echo "3. Push to registry:"
echo "   docker push ${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}/orchestrator:latest"
echo ""
echo "4. Deploy to Cloud Run:"
echo "   gcloud run deploy orchestrator \\"
echo "     --image ${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}/orchestrator:latest \\"
echo "     --region ${REGION}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 7 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Repository URL:"
echo "  ${REGISTRY_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}"
echo ""
echo "Artifact Registry Console:"
echo "  https://console.cloud.google.com/artifacts?project=$PROJECT_ID"
echo ""
echo "Next: Run ./08_configure_defaults.sh"
