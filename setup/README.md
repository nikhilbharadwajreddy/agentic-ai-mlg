# 🚀 Phase 1: GCP Foundation Setup

This folder contains everything you need to set up the GCP infrastructure for the AI Agent system.

## 📋 What Phase 1 Does

Phase 1 sets up the **secure foundation** for your production AI agent:

1. ✅ **GCP Project** - Isolated environment for all resources
2. ✅ **APIs** - Enable required GCP services
3. ✅ **Service Accounts** - Secure identities for services
4. ✅ **IAM Permissions** - Least-privilege access control
5. ✅ **Firestore** - Database for user sessions and state
6. ✅ **Secret Manager** - Secure storage for API keys
7. ✅ **Artifact Registry** - Docker image repository
8. ✅ **Default Configs** - Regional settings

---

## 🎯 Prerequisites

Before starting, ensure you have:

- [ ] **Google Cloud account** with billing enabled
- [ ] **gcloud CLI** installed ([Install Guide](https://cloud.google.com/sdk/docs/install))
- [ ] **Terminal access** (Mac Terminal, Linux shell, or WSL on Windows)
- [ ] **~30 minutes** of time

---

## 🚀 Quick Start

### Step 1: Configure Your Environment

```bash
# Copy the environment template
cp .env.template .env

# Edit .env with your values
nano .env  # or use any text editor
```

Edit these values in `.env`:
```bash
PROJECT_ID="ai-agent-prod-2025"        # Choose unique ID
PROJECT_NAME="AI Agent Production"
REGION="us-central1"                   # Or your preferred region
```

### Step 2: Run All Setup Scripts

```bash
# Make all scripts executable
chmod +x *.sh

# Run setup (in order)
./01_create_project.sh
./02_enable_apis.sh
./03_create_service_accounts.sh
./04_grant_permissions.sh
./05_setup_firestore.sh
./06_setup_secrets.sh
./07_setup_artifact_registry.sh
./08_configure_defaults.sh

# Verify everything
./verify_setup.sh
```

### Step 3: Check the Checklist

Open `CHECKLIST.md` and mark off each completed step.

---

## 📂 File Structure

```
setup/
├── README.md                          # This file
├── CHECKLIST.md                       # Track your progress
├── .env.template                      # Environment variables template
├── 01_create_project.sh              # Creates GCP project
├── 02_enable_apis.sh                 # Enables required APIs
├── 03_create_service_accounts.sh     # Creates service accounts
├── 04_grant_permissions.sh           # Grants IAM permissions
├── 05_setup_firestore.sh             # Initializes Firestore
├── 06_setup_secrets.sh               # Sets up Secret Manager
├── 07_setup_artifact_registry.sh     # Creates Docker registry
├── 08_configure_defaults.sh          # Sets default configs
└── verify_setup.sh                   # Validates entire setup
```

---

## 🔍 Detailed Script Explanations

### 01_create_project.sh
**Purpose:** Creates a new GCP project with unique ID  
**Time:** ~2 minutes  
**What it does:**
- Creates project with specified ID
- Sets it as default project
- Links billing account (manual step)

### 02_enable_apis.sh
**Purpose:** Enables all required GCP services  
**Time:** ~2 minutes  
**APIs enabled:**
- Cloud Run (run.googleapis.com)
- Firestore (firestore.googleapis.com)
- Secret Manager (secretmanager.googleapis.com)
- Vertex AI (aiplatform.googleapis.com)
- Cloud DLP (dlp.googleapis.com)
- Cloud Logging (logging.googleapis.com)
- Pub/Sub (pubsub.googleapis.com)
- Cloud Build (cloudbuild.googleapis.com)
- Artifact Registry (artifactregistry.googleapis.com)

### 03_create_service_accounts.sh
**Purpose:** Creates service identities for our services  
**Time:** ~1 minute  
**Service accounts created:**
- `orchestrator-sa` - Main AI orchestrator service
- `tool-executor-sa` - Executes tools and external calls

### 04_grant_permissions.sh
**Purpose:** Grants minimum required permissions  
**Time:** ~2 minutes  
**Permissions for orchestrator-sa:**
- `roles/aiplatform.user` - Access Vertex AI
- `roles/datastore.user` - Read/write Firestore
- `roles/secretmanager.secretAccessor` - Read secrets
- `roles/dlp.user` - Use DLP for PII detection
- `roles/logging.logWriter` - Write logs

### 05_setup_firestore.sh
**Purpose:** Creates Firestore database  
**Time:** ~1 minute  
**Database type:** Native mode (recommended for new projects)

### 06_setup_secrets.sh
**Purpose:** Initializes Secret Manager with placeholders  
**Time:** ~1 minute  
**Secrets created:**
- `jwt-secret` - For JWT token signing
- `otp-api-key` - For OTP service integration

### 07_setup_artifact_registry.sh
**Purpose:** Creates Docker image repository  
**Time:** ~1 minute  
**Configures:** Docker authentication for pushing images

### 08_configure_defaults.sh
**Purpose:** Sets default region and compute zone  
**Time:** ~30 seconds  
**Simplifies:** Future gcloud commands (no need to specify region)

---

## ✅ Verification

After running all scripts, run the verification:

```bash
./verify_setup.sh
```

**Expected output:**
```
✅ Project: ai-agent-prod-2025
✅ APIs: 9/9 enabled
✅ Service Accounts: 2/2 created
✅ Firestore: 1 database found
✅ Secrets: 2/2 created
✅ Artifact Registry: 1 repository found
✅ Default region: us-central1

🎉 Phase 1 Complete! Ready for Phase 2.
```

---

## 🚨 Troubleshooting

### "Project ID already exists"
**Solution:** Choose a different PROJECT_ID in `.env`

### "Billing account not linked"
**Solution:** 
1. Go to https://console.cloud.google.com/billing
2. Click "Link a billing account"
3. Select your billing account

### "Permission denied" errors
**Solution:** Ensure you're logged in with owner/editor role:
```bash
gcloud auth login
gcloud auth application-default login
```

### "API not enabled" errors
**Solution:** Run `02_enable_apis.sh` again, wait 2 minutes

### "Service account already exists"
**Solution:** This is okay - script will use existing ones

---

## 🔐 Security Notes

### What's Secure About This Setup?

1. **Service Accounts** - Each service has its own identity
2. **Least Privilege** - Minimum permissions granted
3. **Secret Manager** - No hardcoded credentials
4. **IAM Bindings** - Explicit access controls
5. **Firestore Native Mode** - Strong consistency guarantees

### What's NOT in This Phase?

- VPC Service Controls (Phase 2)
- DLP Policies (Phase 3)
- Network Security (Phase 2)
- Monitoring/Alerting (Phase 5)

---

## 📊 Cost Estimate

**Phase 1 costs:** ~$0-5/month (mostly free tier)

- Project creation: **Free**
- APIs enabled: **Free**
- Service accounts: **Free**
- Firestore: **Free tier** (1GB storage, 50K reads/day)
- Secret Manager: **$0.06** per secret per month
- Artifact Registry: **$0.10/GB** per month (minimal usage)

**Note:** Main costs come in Phase 2+ when running Cloud Run and Vertex AI.

---

## 🎯 Next Steps

After Phase 1 completes:

1. ✅ Verify with `./verify_setup.sh`
2. ✅ Review `CHECKLIST.md`
3. ✅ Proceed to **Phase 2: Orchestrator Service**

---

## 📞 Need Help?

Common issues and solutions are in the Troubleshooting section above.

---

## 🗂️ Phase Overview

```
Phase 1 (Foundation)     ← YOU ARE HERE
Phase 2 (Orchestrator)   ← Next
Phase 3 (Security & PII)
Phase 4 (Tool Calling)
Phase 5 (Production Deploy)
```

**Estimated total time:** ~20-30 minutes

---

**Let's build! 🔥**
