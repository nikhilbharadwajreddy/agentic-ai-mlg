"""
Deploy ADK Agent to Vertex AI Agent Engine

Usage:
    python deployment/deploy_agent.py --create
    python deployment/deploy_agent.py --update <AGENT_ID>
    python deployment/deploy_agent.py --list
"""

import argparse
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vertexai.agent_engines import AdkApp
from orchestrator.adk_agent import agent


def deploy_agent(create_new=True, agent_id=None):
    """Deploy agent to Vertex AI Agent Engine."""
    
    project_id = os.getenv("GCP_PROJECT_ID", "agentic-ai-mlg")
    location = "us-central1"
    
    print(f"Deploying to project: {project_id}, location: {location}")
    
    # Initialize
    from google.cloud import aiplatform
    aiplatform.init(project=project_id, location=location)
    
    # Create ADK app
    app = AdkApp(agent=agent)
    
    if create_new:
        print("Creating new agent...")
        # Deploy creates a new reasoning engine
        result = app.deploy(
            display_name="mlg_financial_advisor",
            requirements=[
                "google-cloud-firestore==2.14.0"
            ]
        )
        print(f"\n✅ Agent deployed!")
        print(f"Agent ID: {result}")
        print(f"\nSave this ID and update vertex_agent_client.py")
    
    else:
        print(f"Updating existing agent: {agent_id}")
        # Update existing agent
        result = app.deploy(
            reasoning_engine_id=agent_id,
            requirements=[
                "google-cloud-firestore==2.14.0"
            ]
        )
        print(f"\n✅ Agent updated!")
        print(f"Agent ID: {result}")


def list_agents():
    """List all deployed agents."""
    
    project_id = os.getenv("GCP_PROJECT_ID", "agentic-ai-mlg")
    location = "us-central1"
    
    from google.cloud import aiplatform
    aiplatform.init(project=project_id, location=location)
    
    from google.cloud.aiplatform import ReasoningEngine
    
    agents = ReasoningEngine.list()
    
    if not agents:
        print("No agents found.")
        return
    
    print("\n📋 Deployed Agents:")
    for agent in agents:
        print(f"  - {agent.display_name} (ID: {agent.name})")
        print(f"    Created: {agent.create_time}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy ADK agent to Vertex AI")
    parser.add_argument("--create", action="store_true", help="Create new agent")
    parser.add_argument("--update", type=str, help="Update existing agent (provide ID)")
    parser.add_argument("--list", action="store_true", help="List all agents")
    
    args = parser.parse_args()
    
    if args.list:
        list_agents()
    elif args.create:
        deploy_agent(create_new=True)
    elif args.update:
        deploy_agent(create_new=False, agent_id=args.update)
    else:
        print("Usage:")
        print("  python deployment/deploy_agent.py --create")
        print("  python deployment/deploy_agent.py --update <AGENT_ID>")
        print("  python deployment/deploy_agent.py --list")
