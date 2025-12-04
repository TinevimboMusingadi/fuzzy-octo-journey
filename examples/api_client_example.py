"""Example client script demonstrating how to use the V2.0 FastAPI.

This script shows how to:
1. Start a form session
2. Submit answers interactively
3. Get the final result

Run the API server first:
    python -m src.v2.run_api

Then run this script:
    python examples/api_client_example.py
"""

import requests
import json
from typing import Optional


API_BASE_URL = "http://localhost:8000"


def start_form(form_id: str, mode: str = "hybrid") -> Optional[str]:
    """Start a new form session and return session_id."""
    url = f"{API_BASE_URL}/api/forms/start"
    payload = {"form_id": form_id, "mode": mode}
    
    print(f"\n📋 Starting form: {form_id} (mode: {mode})")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        question = data["question"]
        print(f"✅ Session created: {session_id}")
        print(f"\n🤖 Agent: {question}\n")
        return session_id
    else:
        print(f"❌ Error: {response.status_code} - {response.json()}")
        return None


def submit_answer(session_id: str, message: str) -> dict:
    """Submit an answer and return the response."""
    url = f"{API_BASE_URL}/api/forms/answer"
    payload = {"session_id": session_id, "message": message}
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error: {response.status_code} - {response.json()}")
        return {}


def get_result(session_id: str) -> dict:
    """Get the final collected form data."""
    url = f"{API_BASE_URL}/api/forms/result/{session_id}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error: {response.status_code} - {response.json()}")
        return {}


def list_forms() -> list:
    """List all available forms."""
    url = f"{API_BASE_URL}/api/forms/list"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("forms", [])
    else:
        print(f"❌ Error: {response.status_code}")
        return []


def interactive_form_filling(form_id: str, mode: str = "hybrid"):
    """Interactive form filling session."""
    # Start the form
    session_id = start_form(form_id, mode)
    if not session_id:
        return
    
    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "done"]:
                print("\n👋 Ending session...")
                break
            
            # Submit answer
            result = submit_answer(session_id, user_input)
            
            if result.get("is_complete"):
                print("\n✅ Form Complete!")
                print("\n" + "=" * 60)
                print("Collected Data:")
                print("=" * 60)
                
                collected = result.get("collected_fields", {})
                for field_id, data in collected.items():
                    value = data.get("value", "N/A")
                    print(f"  {field_id}: {value}")
                
                # Get full result
                full_result = get_result(session_id)
                if full_result:
                    print("\n📊 Full Result:")
                    print(json.dumps(full_result, indent=2))
                
                break
            else:
                question = result.get("question")
                if question:
                    print(f"\n🤖 Agent: {question}\n")
                else:
                    print("\n⚠️  No question returned, but form is not complete.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Getting current result...")
            result = get_result(session_id)
            if result:
                print("\n📊 Current Progress:")
                print(json.dumps(result, indent=2))
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break


def main():
    """Main entry point."""
    print("=" * 60)
    print("V2.0 API Client Example")
    print("=" * 60)
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"❌ API server is not responding at {API_BASE_URL}")
            print("   Please start the server first:")
            print("   python -m src.v2.run_api")
            return
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to API server at {API_BASE_URL}")
        print("   Please start the server first:")
        print("   python -m src.v2.run_api")
        return
    
    # List available forms
    print("\n📋 Available Forms:")
    forms = list_forms()
    for form in forms:
        print(f"  - {form['id']} ({form.get('field_count', 0)} fields)")
    
    # Example: Run employment onboarding
    print("\n" + "=" * 60)
    print("Starting Employment Onboarding Form (Interactive)")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the session\n")
    
    interactive_form_filling("employment_onboarding", mode="hybrid")


if __name__ == "__main__":
    main()

