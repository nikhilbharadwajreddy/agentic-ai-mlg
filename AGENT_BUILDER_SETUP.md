# VERTEX AI AGENT BUILDER SETUP

## WHY AGENT BUILDER (NOT ADK)?

✅ **True Agentic System** - Not just Gemini function calling
✅ **No Dependency Hell** - No complex Python packages
✅ **Production Ready** - Google's recommended approach
✅ **Visual Builder** - Create agent in console, use via API
✅ **Built-in Tools** - Search, Data Store, Custom Functions

---

## STEP 1: CREATE AGENT IN CONSOLE

1. **Go to**: https://console.cloud.google.com/gen-app-builder/engines
   - Or: Console → Vertex AI → Agent Builder → Agents

2. **Click "Create Agent"**

3. **Agent Settings:**
   - Name: `mlg-financial-advisor`
   - Location: `us-central1`
   - Type: **Agent**
   - Default language: English

4. **Instructions** (paste this):
```
You are an AI assistant for MLG-Financials.

After customer verification, greet them:
"Thanks for your details! You can now ask me general questions about pensions, investments, and financial products. Please keep in mind I can't provide personalized advice. If you'd like personalized guidance, I can book you a call with one of our advisors: Sarah or David."

Your role:
- Answer general questions about pensions, investments, and financial products
- IMPORTANT: Never give personalized financial advice
- Help customers book calls with financial advisors (Sarah or David)
- Be professional, clear, and helpful

When customers want to book a call:
1. Ask: "Would you like to speak with Sarah or David?"
2. Use list_employees tool to show available advisors
3. Use get_employee_availability tool to show their available times
4. Use book_appointment tool to confirm the booking
5. Always confirm: date, time, and advisor name before booking

Keep responses concise and friendly.
```

5. **Click Create**

---

## STEP 2: ADD TOOLS TO AGENT

Tools are Python functions the agent can call. We'll expose them via Cloud Functions.

### Option A: Deploy Tools as Cloud Functions (Recommended)

1. **Create Cloud Function for each tool:**

```bash
# In your project directory
mkdir agent-tools-functions
cd agent-tools-functions
```

2. **Create `main.py`:**

```python
import functions_framework
from google.cloud import firestore
import os

db = firestore.Client(project=os.getenv('GCP_PROJECT_ID', 'agentic-ai-mlg'))

@functions_framework.http
def list_employees(request):
    """List available financial advisors."""
    try:
        employees = db.collection('employees').where('active', '==', True).stream()
        result = [{'id': e.to_dict()['employee_id'], 
                   'name': e.to_dict()['name'],
                   'role': e.to_dict()['role']} 
                  for e in employees]
        return {'employees': result}
    except Exception as e:
        return {'error': str(e)}, 500

@functions_framework.http
def get_employee_availability(request):
    """Get available time slots for advisor."""
    data = request.get_json()
    employee_id = data.get('employee_id')
    date = data.get('date')
    
    try:
        query = db.collection('time_slots')\
            .where('employee_id', '==', employee_id)\
            .where('is_booked', '==', False)
        
        if date:
            query = query.where('date', '==', date)
        
        slots = query.stream()
        result = [{'date': s.to_dict()['date'],
                   'start_time': s.to_dict()['start_time'],
                   'end_time': s.to_dict()['end_time']}
                  for s in slots]
        
        return {'slots': result}
    except Exception as e:
        return {'error': str(e)}, 500

@functions_framework.http
def book_appointment(request):
    """Book appointment with advisor."""
    data = request.get_json()
    employee_id = data.get('employee_id')
    date = data.get('date')
    time = data.get('time')
    customer_id = data.get('customer_id', 'unknown')
    customer_name = data.get('customer_name', 'Customer')
    customer_email = data.get('customer_email', '')
    
    try:
        import uuid
        emp = db.collection('employees').document(employee_id).get()
        if not emp.exists:
            return {'error': 'Advisor not found'}, 404
        
        apt_id = f"apt_{uuid.uuid4().hex[:8]}"
        appointment = {
            'appointment_id': apt_id,
            'customer_id': customer_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'employee_id': employee_id,
            'employee_name': emp.to_dict()['name'],
            'date': date,
            'time': time,
            'purpose': 'Financial Consultation',
            'status': 'confirmed',
            'created_at': firestore.SERVER_TIMESTAMP
        }
        
        db.collection('appointments').document(apt_id).set(appointment)
        
        # Mark slot as booked
        slots = db.collection('time_slots')\
            .where('employee_id', '==', employee_id)\
            .where('date', '==', date)\
            .where('start_time', '==', time)\
            .where('is_booked', '==', False)\
            .limit(1).stream()
        
        for slot in slots:
            slot.reference.update({'is_booked': True})
        
        return {
            'success': True,
            'appointment_id': apt_id,
            'message': f"Appointment booked with {emp.to_dict()['name']} on {date} at {time}"
        }
    except Exception as e:
        return {'error': str(e)}, 500
```

3. **Create `requirements.txt`:**
```
functions-framework==3.*
google-cloud-firestore==2.14.0
```

4. **Deploy each function:**

```bash
# list_employees
gcloud functions deploy list_employees \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point list_employees \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=agentic-ai-mlg

# get_employee_availability
gcloud functions deploy get_employee_availability \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point get_employee_availability \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=agentic-ai-mlg

# book_appointment
gcloud functions deploy book_appointment \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point book_appointment \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=agentic-ai-mlg
```

5. **Get the function URLs:**
```bash
gcloud functions describe list_employees --region us-central1 --format='value(serviceConfig.uri)'
gcloud functions describe get_employee_availability --region us-central1 --format='value(serviceConfig.uri)'
gcloud functions describe book_appointment --region us-central1 --format='value(serviceConfig.uri)'
```

---

## STEP 3: CONNECT TOOLS TO AGENT

1. **In Agent Builder console**, go to your agent

2. **Click "Tools"** in left sidebar

3. **Add Tool** → **OpenAPI**

4. **For each tool, create OpenAPI spec:**

**list_employees:**
```yaml
openapi: 3.0.0
info:
  title: List Employees
  version: 1.0.0
servers:
  - url: YOUR_FUNCTION_URL_HERE
paths:
  /:
    get:
      summary: List available financial advisors
      operationId: list_employees
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  employees:
                    type: array
                    items:
                      type: object
```

**get_employee_availability:**
```yaml
openapi: 3.0.0
info:
  title: Get Employee Availability
  version: 1.0.0
servers:
  - url: YOUR_FUNCTION_URL_HERE
paths:
  /:
    post:
      summary: Get available time slots for advisor
      operationId: get_employee_availability
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_id:
                  type: string
                date:
                  type: string
      responses:
        '200':
          description: Success
```

**book_appointment:**
```yaml
openapi: 3.0.0
info:
  title: Book Appointment
  version: 1.0.0
servers:
  - url: YOUR_FUNCTION_URL_HERE
paths:
  /:
    post:
      summary: Book appointment with advisor
      operationId: book_appointment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_id:
                  type: string
                date:
                  type: string
                time:
                  type: string
                customer_id:
                  type: string
                customer_name:
                  type: string
                customer_email:
                  type: string
      responses:
        '200':
          description: Success
```

---

## STEP 4: GET AGENT ID & UPDATE CODE

1. **In Agent Builder console**, click on your agent

2. **Copy the Agent ID** from the URL or settings
   - Format: `projects/agentic-ai-mlg/locations/us-central1/agents/AGENT_ID`

3. **Update `vertex_agent_client.py`:**
   - Line 32: Set `self.agent_id = "YOUR_AGENT_ID_HERE"`

---

## STEP 5: DEPLOY & TEST

```bash
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg
gcloud builds submit --config cloudbuild.yaml
```

After deployment, use frontend.html to test!

---

## ALTERNATIVE: Skip Tools for Now

If you want to test faster:

1. Create agent WITHOUT tools first
2. Agent will just answer questions about finance (no booking yet)
3. Add tools later when ready

This way you can test the flow immediately!
