"""
Simple test script to verify the orchestrator works locally.
Run this after starting the server to test the workflow.
"""

import requests
import json

BASE_URL = "http://localhost:8080"
USER_ID = "test_user_demo"


def test_health():
    """Test health endpoint"""
    print("\n1. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200


def test_chat(message: str):
    """Send a chat message"""
    print(f"\n   User: {message}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={
            "user_id": USER_ID,
            "message": message
        }
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Bot: {data['response']}")
        print(f"   Current Step: {data['current_step']}")
        print(f"   Completed Steps: {data['completed_steps']}")
    else:
        print(f"   Error: {response.text}")
    
    return response


def test_workflow():
    """Test complete workflow"""
    print("\n2. Testing workflow...")
    
    # Step 1: Terms
    print("\n   STEP 1: Terms and Conditions")
    test_chat("I accept the terms and conditions")
    
    # Step 2: Name
    print("\n   STEP 2: Name Collection")
    test_chat("My name is John Smith")
    
    # Step 3: Email
    print("\n   STEP 3: Email Collection")
    test_chat("john.smith@example.com")
    
    # Step 4: Phone
    print("\n   STEP 4: Phone Collection")
    test_chat("555-123-4567")
    
    # Step 5: OTP
    print("\n   STEP 5: OTP Verification")
    test_chat("123456")
    
    # Step 6: Active conversation
    print("\n   STEP 6: Active Conversation")
    test_chat("What can you help me with?")


def test_tools():
    """Test tool calling"""
    print("\n3. Testing tool calls...")
    
    response = requests.post(f"{BASE_URL}/api/v1/tools/list")
    print(f"   Available tools: {response.json()}")


def test_state():
    """Test state retrieval"""
    print("\n4. Testing state retrieval...")
    
    response = requests.get(f"{BASE_URL}/api/v1/state/{USER_ID}")
    print(f"   User state: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("=" * 60)
    print("AI AGENT ORCHESTRATOR - TEST SUITE")
    print("=" * 60)
    
    try:
        test_health()
        test_workflow()
        test_tools()
        test_state()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
    
    except Exception as e:
        print(f"\nTest failed: {e}")
        print("Make sure the server is running: python -m orchestrator.main")
