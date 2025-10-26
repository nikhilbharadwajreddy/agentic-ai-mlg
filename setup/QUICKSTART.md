# ⚡ Quick Start Guide - Phase 1

**Time required:** 15-20 minutes  
**Goal:** Set up secure GCP infrastructure for AI Agent

---

## 🚀 Steps (Copy-Paste Friendly)

### 1️⃣ Navigate to setup folder
```bash
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg/setup
```

### 2️⃣ Create your configuration
```bash
# Copy template
cp .env.template .env

# Edit with your favorite editor
nano .env
# OR
code .env
# OR
vim .env
```

**Required changes in `.env`:**
- `PROJECT_ID` → Choose unique ID (e.g., `ai-agent-prod-2025`)
- `PROJECT_NAME` → Your project name
- `REGION` → Keep `us-central1` or choose closer region

### 3️⃣ Run everything at once
```bash
# Make scripts executable
chmod +x *.sh

# Run all steps
./run_all.sh
```

**OR run step-by-step:**
```bash
chmod +x *.sh
./01_create_project.sh
./02_enable_apis.sh
./03_create_service_accounts.sh
./04_grant_permissions.sh
./05_setup_firestore.sh
./06_setup_secrets.sh
./07_setup_artifact_registry.sh
./08_configure_defaults.sh
./verify_setup.sh
```

### 4️⃣ Verify completion
```bash
./verify_setup.sh
```

Expected output:
```
Checks passed: X / X
🎉 All checks passed! Phase 1 is complete!
```

---

## 📋 What Gets Created

| Resource | Description |
|----------|-------------|
| GCP Project | Isolated environment |
| Firestore | Database for user sessions |
| Secret Manager | Secure API key storage |
| Service Accounts | Identities for services |
| Artifact Registry | Docker image storage |
| IAM Permissions | Least-privilege access |

---

## 🔗 Important URLs (After Setup)

All links will be in `../config_summary.txt`

Quick access:
```bash
# View configuration summary
cat ../config_summary.txt

# Open GCP Console
open "https://console.cloud.google.com/home/dashboard?project=$(gcloud config get-value project)"
```

---

## 🚨 If Something Fails

1. **Read the error message** - It usually tells you what's wrong
2. **Check billing** - Most common issue
3. **Re-run the failed script** - Scripts are idempotent (safe to re-run)
4. **Wait 2 minutes** - APIs need time to enable
5. **Check README.md** - Full troubleshooting guide

---

## ✅ Success Criteria

You're done when:
- [ ] `./verify_setup.sh` shows 100% pass
- [ ] No errors in console output
- [ ] `../config_summary.txt` exists
- [ ] You can see resources in GCP Console

---

## ➡️ What's Next?

After Phase 1:
1. Review `CHECKLIST.md` 
2. Save important URLs from `config_summary.txt`
3. **Ready for Phase 2** - Building the Orchestrator!

---

## 💰 Cost Estimate

Phase 1 resources cost **~$0-5/month** (mostly free tier)

Main costs start in Phase 2 when running:
- Cloud Run services
- Vertex AI (Gemini) calls

---

## 🆘 Need Help?

1. Check `README.md` for detailed explanations
2. Review script comments
3. Verify in GCP Console manually
4. All scripts have built-in error messages

---

**Let's go! 🔥**
