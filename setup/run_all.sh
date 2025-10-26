#!/bin/bash

# ============================================================================
# Script: run_all.sh
# Purpose: Run all Phase 1 setup scripts in sequence
# Time: ~15-20 minutes total
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}   Phase 1: GCP Foundation Setup${NC}"
echo -e "${BOLD}   Running All Steps Sequentially${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo ""
    echo "Please create .env first:"
    echo "  cp .env.template .env"
    echo "  # Edit .env with your values"
    echo ""
    exit 1
fi

# Make all scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x *.sh
echo -e "${GREEN}✅ Scripts are executable${NC}"
echo ""

# Confirmation
echo -e "${YELLOW}⚠️  This will run all 8 setup steps.${NC}"
echo ""
echo "Steps to be executed:"
echo "  1. Create GCP Project"
echo "  2. Enable APIs"
echo "  3. Create Service Accounts"
echo "  4. Grant IAM Permissions"
echo "  5. Setup Firestore"
echo "  6. Setup Secret Manager"
echo "  7. Setup Artifact Registry"
echo "  8. Configure Defaults"
echo ""
echo "Estimated time: 15-20 minutes"
echo ""
read -p "Press ENTER to continue or Ctrl+C to cancel..."

echo ""
echo -e "${BLUE}Starting Phase 1 setup...${NC}"
echo ""
sleep 2

# Track start time
START_TIME=$(date +%s)

# Run each script
SCRIPTS=(
    "01_create_project.sh"
    "02_enable_apis.sh"
    "03_create_service_accounts.sh"
    "04_grant_permissions.sh"
    "05_setup_firestore.sh"
    "06_setup_secrets.sh"
    "07_setup_artifact_registry.sh"
    "08_configure_defaults.sh"
)

for script in "${SCRIPTS[@]}"; do
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Running: $script${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    
    ./"$script"
    
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}❌ Error: $script failed!${NC}"
        echo "Please fix the issue and re-run this script."
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}✅ $script completed successfully${NC}"
    echo ""
    sleep 2
done

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${BLUE}Running Final Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""

./verify_setup.sh

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}   🎉 PHASE 1 COMPLETE! 🎉${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Total time: ${MINUTES}m ${SECONDS}s${NC}"
    echo ""
    echo "📄 Configuration saved to: ../config_summary.txt"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Review ../config_summary.txt"
    echo "  2. Mark items in CHECKLIST.md as complete"
    echo "  3. Proceed to Phase 2 (Orchestrator Service)"
    echo ""
    echo -e "${BOLD}You're ready to build! 🚀${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Phase 1 setup completed but verification found issues.${NC}"
    echo "Please review the verification output above."
    echo ""
fi
