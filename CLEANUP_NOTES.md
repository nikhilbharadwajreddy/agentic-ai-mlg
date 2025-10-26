# CLEANUP - OLD FILES

## Files No Longer Needed (Can Delete)

These files are from the old custom agent implementation and are replaced by Vertex AI Agent:

1. `orchestrator/agents/appointment_agent.py` - ❌ Not used
2. `orchestrator/agents/company_info_agent.py` - ❌ Not used  
3. `orchestrator/agents/main_agent.py` - ❌ Not used
4. `orchestrator/agents/base.py` - ❌ Not used

**Keep:**
- `orchestrator/agents/__init__.py` - ✅ Keep (Python needs it)

## To Delete (Optional)

```bash
cd /Users/bharadwajreddy/Desktop/MLG-re/agentic-ai-mlg
rm orchestrator/agents/appointment_agent.py
rm orchestrator/agents/company_info_agent.py
rm orchestrator/agents/main_agent.py
rm orchestrator/agents/base.py
```

Or keep them for reference - they won't interfere with the new system.
