#!/bin/bash

# ============================================================================
# Script: verify_setup.sh
# Purpose: Verify all Phase 1 setup steps completed successfully
# Time: ~1 minute
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================"
echo "  Phase 1 Verification"
echo "============================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}❌ Error: .env file not found${NC}"
    exit 1
fi

TOTAL_CHECKS=0
PASSED_CHECKS=0

# Helper function
check_pass() {
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    ((TOTAL_CHECKS++))
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# 1. PROJECT CHECK
# ============================================================================
echo -e "${BLUE}[1/8] Checking Project...${NC}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" = "$PROJECT_ID" ]; then
    check_pass "Project configured: $PROJECT_ID"
else
    check_fail "Project not set correctly (expected: $PROJECT_ID, got: $CURRENT_PROJECT)"
fi

# Check billing
if gcloud beta billing projects describe $PROJECT_ID &> /dev/null; then
    check_pass "Billing account linked"
else
    check_fail "Billing account not linked"
fi

echo ""

# ============================================================================
# 2. APIS CHECK
# ============================================================================
echo -e "${BLUE}[2/8] Checking APIs...${NC}"
REQUIRED_APIS=(
    "run.googleapis.com"
    "firestore.googleapis.com"
    "secretmanager.googleapis.com"
    "aiplatform.googleapis.com"
    "dlp.googleapis.com"
    "logging.googleapis.com"
    "artifactregistry.googleapis.com"
)

ENABLED_API_COUNT=0
for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        ((ENABLED_API_COUNT++))
    fi
done

if [ $ENABLED_API_COUNT -eq ${#REQUIRED_APIS[@]} ]; then
    check_pass "All ${#REQUIRED_APIS[@]} required APIs enabled"
else
    check_fail "Only $ENABLED_API_COUNT/${#REQUIRED_APIS[@]} APIs enabled"
fi

echo ""

# ============================================================================
# 3. SERVICE ACCOUNTS CHECK
# ============================================================================
echo -e "${BLUE}[3/8] Checking Service Accounts...${NC}"
ORCHESTRATOR_EMAIL="${ORCHESTRATOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com"
TOOL_EXECUTOR_EMAIL="${TOOL_EXECUTOR_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$ORCHESTRATOR_EMAIL" &> /dev/null; then
    check_pass "Orchestrator service account exists"
else
    check_fail "Orchestrator service account missing"
fi

if gcloud iam service-accounts describe "$TOOL_EXECUTOR_EMAIL" &> /dev/null; then
    check_pass "Tool executor service account exists"
else
    check_fail "Tool executor service account missing"
fi

echo ""

# ============================================================================
# 4. IAM PERMISSIONS CHECK
# ============================================================================
echo -e "${BLUE}[4/8] Checking IAM Permissions...${NC}"
ORCHESTRATOR_ROLES=$(gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:${ORCHESTRATOR_EMAIL}" \
    --format="value(bindings.role)" | wc -l)

if [ "$ORCHESTRATOR_ROLES" -ge 5 ]; then
    check_pass "Orchestrator has sufficient permissions ($ORCHESTRATOR_ROLES roles)"
else
    check_fail "Orchestrator missing permissions (only $ORCHESTRATOR_ROLES roles)"
fi

echo ""

# ============================================================================
# 5. FIRESTORE CHECK
# ============================================================================
echo -e "${BLUE}[5/8] Checking Firestore...${NC}"
if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "(default)"; then
    DB_TYPE=$(gcloud firestore databases describe --database="(default)" --format="value(type)" 2>/dev/null)
    if [ "$DB_TYPE" = "FIRESTORE_NATIVE" ]; then
        check_pass "Firestore Native mode database exists"
    else
        check_fail "Firestore exists but not in Native mode (type: $DB_TYPE)"
    fi
else
    check_fail "Firestore database not found"
fi

echo ""

# ============================================================================
# 6. SECRET MANAGER CHECK
# ============================================================================
echo -e "${BLUE}[6/8] Checking Secret Manager...${NC}"
SECRET_COUNT=$(gcloud secrets list --format="value(name)" | wc -l)
if [ "$SECRET_COUNT" -ge 2 ]; then
    check_pass "Secret Manager configured ($SECRET_COUNT secrets)"
    
    # Check specific secrets
    if gcloud secrets describe jwt-secret &> /dev/null; then
        check_pass "jwt-secret exists"
    else
        check_fail "jwt-secret missing"
    fi
else
    check_fail "Insufficient secrets ($SECRET_COUNT found, need at least 2)"
fi

echo ""

# ============================================================================
# 7. ARTIFACT REGISTRY CHECK
# ============================================================================
echo -e "${BLUE}[7/8] Checking Artifact Registry...${NC}"
if gcloud artifacts repositories describe $REGISTRY_NAME --location=$REGISTRY_LOCATION &> /dev/null; then
    check_pass "Artifact Registry repository exists"
else
    check_fail "Artifact Registry repository not found"
fi

echo ""

# ============================================================================
# 8. DEFAULT CONFIGURATION CHECK
# ============================================================================
echo -e "${BLUE}[8/8] Checking Default Configuration...${NC}"
DEFAULT_REGION=$(gcloud config get-value run/region 2>/dev/null)
if [ "$DEFAULT_REGION" = "$REGION" ]; then
    check_pass "Default region configured: $REGION"
else
    check_fail "Default region not set correctly"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo "============================================"
echo -e "  ${BLUE}Verification Summary${NC}"
echo "============================================"
echo ""
echo "Checks passed: $PASSED_CHECKS / $TOTAL_CHECKS"
echo ""

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}🎉 All checks passed! Phase 1 is complete!${NC}"
    echo ""
    echo "You are ready to proceed to Phase 2."
    echo ""
    echo "Next steps:"
    echo "  1. Review ../config_summary.txt"
    echo "  2. Start building the orchestrator service (Phase 2)"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed. Please review and fix issues.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Re-run failed setup scripts"
    echo "  • Check billing is enabled"
    echo "  • Wait 1-2 minutes for APIs to fully enable"
    echo ""
    exit 1
fi
