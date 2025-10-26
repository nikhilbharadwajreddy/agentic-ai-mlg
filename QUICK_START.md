# 🚀 QUICK START GUIDE

## SETUP (Do Once)

### 1. Create Vertex AI Agent in GCP Console
- Go to: Vertex AI > Agent Builder > Create Agent
- Name: `mlground-assistant`
- Copy the resource name after creation
- Update `orchestrator/vertex_agent_client.py` line 22 with agent ID

### 2. Create Firestore Indexes
```bash
gcloud firestore indexes composite create \
  --collection-group=time_slots \
  --field-config field-path=employee_id,order=ASCENDING \
  --field-config field-path=is_booked,order=ASCENDING \
  --field-config field-path=date,order=ASCENDING

gcloud firestore indexes composite create \
  --collection-group=appointments \
  --field-config field-path=date,order=ASCENDING \
  --field-config field-path=time,order=ASCENDING
```

### 3. Grant Permissions
```bash
gcloud projects add-iam-policy-binding agentic-ai-mlg \
  --member="serviceAccount:orchestrator-sa@agentic-ai-mlg.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

---

## RUN LOCALLY

```bash
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg
export GCP_PROJECT_ID=agentic-ai-mlg
python -m orchestrator.main
```

Server runs at: http://localhost:8080

---

## ADMIN SETUP (Add Sales Reps & Slots)

### Add Employee
```bash
curl -X POST http://localhost:8080/api/v1/admin/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Johnson",
    "role": "Senior Sales Rep",
    "email": "sarah@mlground.com"
  }'

# Response: {"success": true, "employee": {"employee_id": "emp_abc123", ...}}
```

### Add Time Slots
```bash
# Use employee_id from above
curl -X POST http://localhost:8080/api/v1/admin/slots \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "emp_abc123",
    "date": "2025-11-01",
    "start_time": "09:00",
    "end_time": "09:30"
  }'

# Add more slots
curl -X POST http://localhost:8080/api/v1/admin/slots \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "emp_abc123",
    "date": "2025-11-01",
    "start_time": "10:00",
    "end_time": "10:30"
  }'
```

### View All Appointments
```bash
curl http://localhost:8080/api/v1/admin/appointments
```

---

## CUSTOMER FLOW

### 1. Start Chat (Auth Flow)
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "TERMS_ACCEPTED"}'

# Response: "Great! What's your name?"
```

### 2. Provide Name
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "John Smith"}'

# Response: "Nice to meet you, John Smith! What's your email?"
```

### 3. Provide Email
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "john@example.com"}'

# Response: "Perfect! Now I need your phone with country code."
```

### 4. Provide Phone
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "+1 555-123-4567"}'

# Response: "I've sent a code to john@example.com"
# Check console logs for OTP (in mock mode)
```

### 5. Enter OTP
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "123456"}'

# Response: "Verification complete! How can I help?"
# NOW CUSTOMER IS ACTIVE - Agent takes over
```

### 6. Book Appointment (Agent Handles)
```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "I want to book a demo"}'

# Agent: "Who would you like to meet with? We have: Sarah Johnson (Sales Rep)"
```

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "Sarah Johnson"}'

# Agent: "Available slots for Sarah: Nov 1 9:00am, 10:00am..."
```

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "customer_001", "message": "Book Nov 1 at 9am"}'

# Agent: "Done! Booked with Sarah Johnson on Nov 1 at 9:00am"
```

---

## DEPLOY TO CLOUD RUN

```bash
gcloud builds submit --config cloudbuild.yaml
```

---

## TROUBLESHOOTING

**Issue:** Agent not responding properly
- Check agent is created in Vertex AI console
- Verify agent resource name in `vertex_agent_client.py`
- Check service account has `roles/aiplatform.user`

**Issue:** No employees/slots showing
- Use admin APIs to add employees and slots first
- Check Firestore console for data

**Issue:** Booking fails
- Verify Firestore indexes are created (takes 5-10 minutes)
- Check employee_id and slot exist

**Issue:** OTP not received
- In local mode, OTP is logged to console (mock mode)
- For real emails, set SendGrid API key in Secret Manager
