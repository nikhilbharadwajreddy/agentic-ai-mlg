#!/bin/bash

# ============================================================================
# Script: 05_setup_firestore.sh
# Purpose: Initialize Firestore database in Native mode
# Time: ~1 minute
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo "  Step 5: Setup Firestore Database"
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

echo -e "${YELLOW}📊 Creating Firestore database...${NC}"
echo ""
echo "Database type: $FIRESTORE_TYPE"
echo "Location: $FIRESTORE_LOCATION"
echo ""

# Check if Firestore already exists
if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "(default)"; then
    echo -e "${YELLOW}⚠️  Firestore database already exists${NC}"
    
    # Get existing database info
    EXISTING_TYPE=$(gcloud firestore databases describe --database="(default)" --format="value(type)" 2>/dev/null || echo "unknown")
    EXISTING_LOCATION=$(gcloud firestore databases describe --database="(default)" --format="value(locationId)" 2>/dev/null || echo "unknown")
    
    echo "Existing database:"
    echo "  Type: $EXISTING_TYPE"
    echo "  Location: $EXISTING_LOCATION"
    
    if [ "$EXISTING_TYPE" != "FIRESTORE_NATIVE" ]; then
        echo -e "${RED}⚠️  WARNING: Database is not in Native mode!${NC}"
        echo "You're using Datastore mode. This may cause compatibility issues."
        echo "Consider creating a new project for native Firestore."
    fi
else
    echo "Creating Firestore Native database..."
    
    # Create Firestore database
    gcloud firestore databases create \
        --location=$FIRESTORE_LOCATION \
        --type=$FIRESTORE_TYPE
    
    echo -e "${GREEN}✅ Firestore database created!${NC}"
    
    # Wait for creation to complete
    echo "Waiting for database to be ready..."
    sleep 5
fi

# Verify database
echo ""
echo -e "${YELLOW}🔍 Verifying Firestore setup...${NC}"
DB_INFO=$(gcloud firestore databases describe --database="(default)" --format="table(name,type,locationId)" 2>/dev/null)

if [ -n "$DB_INFO" ]; then
    echo "$DB_INFO"
    echo -e "${GREEN}✅ Firestore is ready!${NC}"
else
    echo -e "${RED}❌ Could not verify Firestore database${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📝 Collections that will be created:${NC}"
echo "  • users          - User profiles and preferences"
echo "  • sessions       - Active conversation sessions"
echo "  • conversations  - Conversation history"
echo "  • tool_results   - Tool execution results"
echo "  • audit_logs     - Security audit trail"
echo ""
echo "(Collections are created automatically when first written to)"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Step 5 Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Firestore Console: https://console.cloud.google.com/firestore/data?project=$PROJECT_ID"
echo ""
echo "Next: Run ./06_setup_secrets.sh"
