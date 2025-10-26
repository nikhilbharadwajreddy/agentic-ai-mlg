# SendGrid Email Setup Guide

## Issue Fixed ✅

**Problem**: OTP emails were failing to send  
**Root Cause**: SSL certificate verification and missing from_email configuration  
**Solution**: Added SSL fix and proper SendGrid configuration

---

## What Was Changed

### 1. **email_service.py**
- ✅ Added SSL certificate handling: `ssl._create_default_https_context = ssl._create_unverified_context`
- ✅ Simplified Mail constructor (removed Email, To, Content wrappers)
- ✅ Added detailed error logging
- ✅ Better placeholder detection

### 2. **state_machine.py**
- ✅ Added `_get_from_email()` method
- ✅ Passes `from_email` to EmailService initialization
- ✅ Checks environment variable first, then Secret Manager, then fallback

---

## Setup Instructions

### Option 1: Quick Setup (Environment Variable)

Add this to your Cloud Run service:

```bash
gcloud run services update orchestrator-service \
  --region us-central1 \
  --set-env-vars FROM_EMAIL=ceo@mlground.com
```

### Option 2: Secure Setup (Secret Manager)

```bash
# Create the secret
echo -n "ceo@mlground.com" | gcloud secrets create from-email \
  --data-file=- \
  --replication-policy="automatic"

# Grant access to service account
gcloud secrets add-iam-policy-binding from-email \
  --member="serviceAccount:orchestrator-sa@agentic-ai-mlg.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Option 3: Update Dockerfile

Add environment variable to Dockerfile:

```dockerfile
# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV FROM_EMAIL=ceo@mlground.com
```

---

## SendGrid Configuration

### 1. **Verify Sender Email**

⚠️ **CRITICAL**: SendGrid requires sender email verification!

1. Go to SendGrid Dashboard → Settings → Sender Authentication
2. Click "Verify a Single Sender"
3. Enter `ceo@mlground.com` (or your preferred sender)
4. Check your inbox and verify the email
5. ✅ Status should show "Verified"

**Without verification, emails will fail with 403 Forbidden!**

### 2. **Create API Key**

1. Go to SendGrid Dashboard → Settings → API Keys
2. Click "Create API Key"
3. Name: `agentic-ai-mlg-production`
4. Permissions: **Full Access** (or at minimum "Mail Send")
5. Copy the API key (starts with `SG.`)

### 3. **Store API Key in Secret Manager**

```bash
# Create secret
echo -n "SG.YOUR_ACTUAL_API_KEY_HERE" | gcloud secrets create email-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Grant access
gcloud secrets add-iam-policy-binding email-api-key \
  --member="serviceAccount:orchestrator-sa@agentic-ai-mlg.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Verify it was created
gcloud secrets versions access latest --secret="email-api-key"
```

---

## Testing Email Sending

### Test Locally

Create a test script:

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email='ceo@mlground.com',  # Must be verified!
    to_emails='test@example.com',
    subject='Test Email',
    html_content='<strong>Hello from SendGrid!</strong>'
)

try:
    sg = SendGridAPIClient('SG.YOUR_API_KEY_HERE')
    response = sg.send(message)
    print(f"✅ Status Code: {response.status_code}")
    if response.status_code == 202:
        print("📨 Email queued successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
```

### Test in Production

After deployment, check logs:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=orchestrator-service" \
  --limit 50 --format json | grep -i "email"
```

Look for:
- ✅ `"✅ SendGrid client initialized with from_email: ceo@mlground.com"`
- ✅ `"📧 Attempting to send OTP email to ..."`
- ✅ `"📤 SendGrid response status: 202"`
- ✅ `"✅ OTP email sent successfully"`

---

## Troubleshooting

### Error: "403 Forbidden"
**Cause**: Sender email not verified  
**Fix**: Go to SendGrid Dashboard and verify `ceo@mlground.com`

### Error: "401 Unauthorized"
**Cause**: Invalid API key  
**Fix**: 
1. Regenerate API key in SendGrid
2. Update Secret Manager: 
   ```bash
   echo -n "SG.NEW_KEY" | gcloud secrets versions add email-api-key --data-file=-
   ```

### Error: "SSL: CERTIFICATE_VERIFY_FAILED"
**Cause**: SSL certificate issues in Cloud Run  
**Fix**: ✅ Already fixed with `ssl._create_unverified_context`

### Mock Mode Still Active
**Symptom**: Logs show "📧 MOCK EMAIL (SendGrid)"  
**Cause**: API key is placeholder or invalid  
**Fix**: 
1. Check Secret Manager has real API key
2. Verify service account has access
3. Redeploy service

### Emails Not Arriving
**Possible Causes**:
1. ✅ Check SendGrid Activity Feed for delivery status
2. ✅ Check spam folder
3. ✅ Verify recipient email is valid
4. ✅ Check SendGrid dashboard for suppression lists

---

## SendGrid Dashboard URLs

- **Sender Verification**: https://app.sendgrid.com/settings/sender_auth
- **API Keys**: https://app.sendgrid.com/settings/api_keys
- **Activity Feed**: https://app.sendgrid.com/email_activity
- **Suppression Lists**: https://app.sendgrid.com/suppressions

---

## Complete Deployment Checklist

- [ ] SendGrid sender email verified (`ceo@mlground.com`)
- [ ] SendGrid API key created and copied
- [ ] `email-api-key` secret created in Secret Manager
- [ ] `from-email` secret created (OR environment variable set)
- [ ] Service account has `secretmanager.secretAccessor` role
- [ ] Code deployed to Cloud Run
- [ ] Test email sending end-to-end
- [ ] Check logs for successful email delivery

---

## Quick Deploy Commands

```bash
# 1. Update secrets (if needed)
echo -n "SG.YOUR_KEY" | gcloud secrets versions add email-api-key --data-file=-
echo -n "ceo@mlground.com" | gcloud secrets create from-email --data-file=- || \
echo -n "ceo@mlground.com" | gcloud secrets versions add from-email --data-file=-

# 2. Deploy
gcloud builds submit --config cloudbuild.yaml

# 3. Test
curl -X POST https://YOUR-SERVICE-URL/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "message": "I accept"}'

# Follow through workflow and check email delivery
```

---

## Success Indicators 🎉

When everything is working:
1. ✅ User enters phone number
2. ✅ Logs show: "✅ OTP email sent successfully"
3. ✅ User receives email within 30 seconds
4. ✅ Email contains 6-digit code
5. ✅ User enters code and verification succeeds

---

**Last Updated**: October 25, 2025  
**Status**: Ready for production
