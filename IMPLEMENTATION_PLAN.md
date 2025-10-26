# IMPLEMENTATION PLAN
## Architecture Reversal & Feature Addition

---

## 📊 CURRENT STATE ANALYSIS

### What Exists:
- ✅ Basic FastAPI app with endpoints
- ✅ State machine with workflow steps
- ✅ LLM client using Vertex AI (text-bison - NEEDS UPDATE to Flash 2)
- ✅ Security manager with JWT and DLP
- ✅ Tool registry for appointments
- ✅ Firestore integration for user_states

### What's WRONG (Architecture):
❌ **LLM extracts/validates data** → Then hardcoded responses
   - Uses `extract_structured_data()` for validation
   - Returns hardcoded strings like "Thank you for accepting..."

### What's NEEDED (Correct Architecture):
✅ **Code validates data** → Then LLM generates natural responses
   - Deterministic validation in code
   - LLM only for natural language responses
   - **EXCEPTION**: Name validation uses LLM (complex parsing)

---

## 🎯 CHANGES REQUIRED

### 1. **CREATE NEW MODULES**

#### A. `orchestrator/validators/` (NEW DIRECTORY)
- `__init__.py` - Export all validators
- `name_validator.py` - **Uses LLM** to parse and validate full name
- `email_validator.py` - Regex + DB check for returning users
- `phone_validator.py` - Uses `phonenumbers` library
- `otp_validator.py` - Hash generation/comparison

#### B. `orchestrator/services/` (NEW DIRECTORY)
- `__init__.py` - Export all services
- `email_service.py` - SendGrid integration for OTP emails
- `user_service.py` - CRUD operations for users collection

---

### 2. **UPDATE EXISTING FILES**

#### A. `orchestrator/models.py`
**CHANGES:**
- Add `User` model for users collection
- Add `ValidationResult` model
- Add `OTPData` model
- Keep existing models intact

**NO BREAKING CHANGES** - Only additions

---

#### B. `orchestrator/llm_client.py`
**CHANGES:**
1. Update model from `text-bison` to `gemini-2.0-flash-001`
2. Add `generate_response()` method for conversational responses
3. Keep `extract_structured_data()` for name parsing only
4. Add `validate_name()` method specifically for name detection

**REASONING**: 
- Model needs update (user confirmed Flash 2)
- Need dedicated method for response generation
- Keep extraction only for name parsing

---

#### C. `orchestrator/state_machine.py`
**MAJOR REWRITE:**

**BEFORE (Current):**
```python
def _handle_name(state, message):
    extracted = llm_client.extract_structured_data(...)  # LLM validation
    if name and len(name) > 1:
        return "Nice to meet you, {name}! What is your email?"  # Hardcoded
```

**AFTER (New):**
```python
def _handle_name(state, message):
    # 1. LLM validates name (detects first + last)
    result = name_validator.validate(message, llm_client)
    
    if result.success:
        state.data["first_name"] = result.data["first_name"]
        state.data["last_name"] = result.data["last_name"]
        state.current_step = WorkflowStep.AWAITING_EMAIL
        
        # 2. LLM generates natural response
        response = llm_client.generate_response(
            context={
                "step": "name_collected",
                "first_name": result.data["first_name"]
            }
        )
        return response, state
    else:
        # LLM asks for full name naturally
        response = llm_client.generate_response(
            context={"step": "name_incomplete", "error": result.error_message}
        )
        return response, state
```

**CHANGES TO EACH HANDLER:**
- `_handle_terms()` - Just transition, LLM generates response
- `_handle_name()` - LLM validates + LLM responds
- `_handle_email()` - Code validates + DB check + LLM responds (with masked phone if returning)
- `_handle_phone()` - Code validates + LLM responds
- `_handle_otp()` - Code validates + LLM responds

---

#### D. `orchestrator/security.py`
**CHANGES:**
- Add `mask_phone()` method for displaying partial phone
- Keep all existing security features

---

#### E. `requirements.txt`
**ADD:**
```
sendgrid==6.11.0          # Email OTP
phonenumbers==8.13.26     # Phone validation
```

---

### 3. **CREATE NEW SECRETS**

**In Secret Manager:**
```bash
# Email API Key
gcloud secrets create email-api-key --data-file=-
# Value: "PLACEHOLDER_SENDGRID_API_KEY"

# OTP Salt for hashing
gcloud secrets create otp-salt --data-file=-
# Value: Random string for hashing
```

---

### 4. **FIRESTORE CHANGES**

**NEW COLLECTION: `users`**
```
users/
  {user_id}/
    - email (indexed)
    - first_name
    - last_name (indexed)
    - phone
    - country_code
    - verified: bool
    - created_at: timestamp
    - last_login: timestamp
```

**CREATE COMPOSITE INDEX:**
```bash
gcloud firestore indexes composite create \
  --collection-group=users \
  --field-config field-path=email,order=ASCENDING \
  --field-config field-path=last_name,order=ASCENDING
```

---

## 📝 IMPLEMENTATION ORDER

### Phase 1: Setup (No Breaking Changes)
1. ✅ Create `validators/` directory + `__init__.py`
2. ✅ Create `services/` directory + `__init__.py`
3. ✅ Update `requirements.txt`
4. ✅ Add new models to `models.py`

### Phase 2: Build Validators
5. ✅ Build `name_validator.py` (uses LLM)
6. ✅ Build `email_validator.py` (regex + DB)
7. ✅ Build `phone_validator.py` (phonenumbers)
8. ✅ Build `otp_validator.py` (hash logic)

### Phase 3: Build Services
9. ✅ Build `email_service.py` (SendGrid)
10. ✅ Build `user_service.py` (Firestore CRUD)

### Phase 4: Update Core
11. ✅ Update `llm_client.py` (Flash 2 + generate_response)
12. ✅ Add mask_phone to `security.py`
13. ✅ **REWRITE** `state_machine.py` (use validators + LLM responses)

### Phase 5: Testing
14. ✅ Update `main.py` if needed
15. ✅ Local testing
16. ✅ Deploy to Cloud Run

---

## 🔍 KEY DESIGN DECISIONS

### 1. **Why LLM for Name Only?**
- Names are complex: "Call me Mike", "I'm Sarah Johnson", "My name is O'Brien"
- LLM handles natural language better than regex
- Can detect first vs first+last intelligently

### 2. **Why Code for Email/Phone/OTP?**
- Deterministic validation = reliable
- No hallucination risk
- Security-critical operations

### 3. **Why LLM for ALL Responses?**
- Natural, conversational feel
- Not robotic/scripted
- Adapts to user's tone
- Better user experience

### 4. **Returning User Flow**
```
1. User enters email: john@example.com
2. Code validates format ✓
3. DB query: WHERE email="john@example.com" AND last_name="Smith"
4. IF FOUND:
   - LLM generates: "Welcome back, John!"
   - Backend masks: "+1 555-***-4567"
   - Backend injects: "Is +1 555-***-4567 still correct?"
5. ELSE:
   - LLM generates: Natural transition to phone collection
```

---

## 🚨 CRITICAL RULES

### DO:
✅ Use LLM for name parsing (complex)
✅ Use LLM for ALL response generation
✅ Use code for email/phone/OTP validation
✅ Mask phone numbers before display
✅ Keep existing security features
✅ Add proper error handling
✅ Clean, modular code

### DON'T:
❌ Break existing endpoints
❌ Remove security features
❌ Let LLM see full phone numbers
❌ Let LLM validate OTP
❌ Hardcode responses
❌ Skip input validation

---

## 📁 FINAL FILE STRUCTURE

```
orchestrator/
├── __init__.py
├── main.py                    # (Minor updates only)
├── models.py                  # (Add new models)
├── security.py                # (Add mask_phone)
├── llm_client.py              # (Update model + add generate_response)
├── state_machine.py           # (MAJOR REWRITE)
├── validators/
│   ├── __init__.py
│   ├── name_validator.py      # NEW
│   ├── email_validator.py     # NEW
│   ├── phone_validator.py     # NEW
│   └── otp_validator.py       # NEW
├── services/
│   ├── __init__.py
│   ├── email_service.py       # NEW
│   └── user_service.py        # NEW
└── tools/
    ├── __init__.py
    ├── registry.py            # (Keep as is)
    └── appointments.py        # (Keep as is)
```

---

## ✅ READY TO IMPLEMENT

**Total New Files:** 8
**Modified Files:** 5
**No Breaking Changes:** Endpoints stay same

**Estimated Time:** 2-3 hours of careful implementation

---

## 🎯 SUCCESS CRITERIA

After implementation:
1. ✅ Code validates (except name)
2. ✅ LLM generates ALL responses
3. ✅ Name parsing uses LLM intelligently
4. ✅ Email OTP works
5. ✅ Returning users detected
6. ✅ Phone numbers masked
7. ✅ Flash 2 model used
8. ✅ Clean, maintainable code
9. ✅ All tests pass
10. ✅ Ready to deploy

---

**NEXT STEP:** Get approval, then implement Phase 1!
