# ✅ Phase 1: GCP Foundation Setup Checklist

Use this checklist to track your progress through Phase 1.

---

## 📋 Pre-Setup

- [ ] Google Cloud account created
- [ ] Billing account ready (credit card added)
- [ ] gcloud CLI installed and authenticated
- [ ] Terminal/command line access available
- [ ] ~30 minutes of uninterrupted time

---

## 🔧 Configuration

- [ ] Copied `.env.template` to `.env`
- [ ] Edited `.env` with unique `PROJECT_ID`
- [ ] Chosen appropriate `REGION`
- [ ] Reviewed all configuration values

---

## 🚀 Setup Scripts Execution

### Step 1: Create Project
- [ ] Run: `./01_create_project.sh`
- [ ] Project created successfully
- [ ] Billing account linked
- [ ] Project set as default

**Verification:**
```bash
gcloud config get-value project
# Should output: your-project-id
```

---

### Step 2: Enable APIs
- [ ] Run: `./02_enable_apis.sh`
- [ ] All 9+ APIs enabled
- [ ] No errors in output

**Verification:**
```bash
gcloud services list --enabled | wc -l
# Should show 15+ services
```

---

### Step 3: Create Service Accounts
- [ ] Run: `./03_create_service_accounts.sh`
- [ ] Orchestrator SA created
- [ ] Tool Executor SA created
- [ ] Both visible in IAM

**Verification:**
```bash
gcloud iam service-accounts list
# Should show 2 service accounts with -sa suffix
```

---

### Step 4: Grant IAM Permissions
- [ ] Run: `./04_grant_permissions.sh`
- [ ] Orchestrator has 6 roles
- [ ] Tool executor has 2 roles
- [ ] No permission errors

**Verification:**
```bash
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:*orchestrator-sa*"
# Should show multiple role bindings
```

---

### Step 5: Setup Firestore
- [ ] Run: `./05_setup_firestore.sh`
- [ ] Firestore database created
- [ ] Type: FIRESTORE_NATIVE confirmed
- [ ] Location matches configuration

**Verification:**
```bash
gcloud firestore databases list
# Should show (default) database
```

**Console Check:**
Visit: https://console.cloud.google.com/firestore/data
- [ ] Firestore data viewer loads successfully

---

### Step 6: Setup Secret Manager
- [ ] Run: `./06_setup_secrets.sh`
- [ ] `jwt-secret` created (auto-generated)
- [ ] `otp-api-key` created (placeholder)
- [ ] `vertex-ai-config` created
- [ ] Orchestrator has access to all secrets

**Verification:**
```bash
gcloud secrets list
# Should show 3 secrets
```

**Note:** Update `otp-api-key` later when you have real credentials:
```bash
echo -n 'your-real-key' | gcloud secrets versions add otp-api-key --data-file=-
```

---

### Step 7: Setup Artifact Registry
- [ ] Run: `./07_setup_artifact_registry.sh`
- [ ] Docker repository created
- [ ] Docker authentication configured
- [ ] Can push/pull images

**Verification:**
```bash
gcloud artifacts repositories list
# Should show ai-agent-repo
```

---

### Step 8: Configure Defaults
- [ ] Run: `./08_configure_defaults.sh`
- [ ] Default project set
- [ ] Default region set
- [ ] Default zone set
- [ ] Configuration summary created

**Verification:**
```bash
gcloud config list
# Check all defaults are set correctly
```

---

## ✅ Final Verification

- [ ] Run: `./verify_setup.sh`
- [ ] All checks passed (should show 100%)
- [ ] No critical errors or warnings

**Expected Output:**
```
Checks passed: X / X
🎉 All checks passed! Phase 1 is complete!
```

---

## 📄 Documentation Review

- [ ] Reviewed `../config_summary.txt`
- [ ] Saved important URLs (Firestore, Secret Manager, etc.)
- [ ] Bookmarked GCP Console for quick access
- [ ] Documented any customizations or issues

---

## 🎯 Ready for Phase 2?

Before proceeding to Phase 2, ensure:

- [ ] ✅ All checklist items above are complete
- [ ] ✅ `verify_setup.sh` shows 100% pass rate
- [ ] ✅ No outstanding errors or warnings
- [ ] ✅ Billing is enabled and working
- [ ] ✅ You can access GCP Console without issues

---

## 🚨 Troubleshooting

If any step fails, refer to:

1. **Script output** - Read error messages carefully
2. **README.md** - Check troubleshooting section
3. **GCP Console** - Verify resources manually
4. **Re-run scripts** - Most scripts are idempotent (safe to re-run)

Common issues:
- Billing not linked → Link billing account manually
- APIs not enabled → Wait 2 minutes and re-run
- Permission denied → Check you're logged in as owner/editor
- Region mismatch → Verify .env file has correct region

---

## 📊 Time Tracking

Track your actual time spent on each step:

| Step | Estimated | Actual | Notes |
|------|-----------|--------|-------|
| Pre-setup | 5 min | ___ | Installing gcloud, etc. |
| Step 1 | 2 min | ___ | Create project |
| Step 2 | 2 min | ___ | Enable APIs |
| Step 3 | 1 min | ___ | Service accounts |
| Step 4 | 2 min | ___ | IAM permissions |
| Step 5 | 1 min | ___ | Firestore |
| Step 6 | 1 min | ___ | Secret Manager |
| Step 7 | 1 min | ___ | Artifact Registry |
| Step 8 | 1 min | ___ | Defaults |
| Verification | 1 min | ___ | Final checks |
| **Total** | **~17 min** | **___** | |

---

## 🎉 Completion

**Phase 1 completed on:** ___________________

**Time spent:** ___________________

**Issues encountered:** 
- 
- 
- 

**Ready for Phase 2?** ☐ YES  ☐ NO (if no, what's blocking?)

---

**Next:** Proceed to Phase 2 - Building the Orchestrator Service

When ready, the instructor will provide Phase 2 setup instructions and code.

---

**Questions or stuck?** Review:
1. `README.md` in this directory
2. Script comments in individual .sh files
3. GCP Console for visual verification
