"""Main entry point for the intake form agent."""

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.graph import create_intake_graph
from src.nodes import set_config
from src.config import AgentConfig

# Load environment variables
load_dotenv()


def create_sample_schema():
    """Create a sample form schema for testing."""
    return {
        "fields": [
            {
                "id": "name",
                "field_type": "text",
                "label": "Full Name",
                "description": "Enter your full legal name",
                "required": True
            },
            {
                "id": "email",
                "field_type": "email",
                "label": "Email Address",
                "description": "We'll use this to contact you",
                "required": True
            },
            {
                "id": "phone",
                "field_type": "phone",
                "label": "Phone Number",
                "description": "Include area code",
                "required": False
            },
            {
                "id": "age",
                "field_type": "number",
                "label": "Age",
                "description": "Your age in years",
                "required": False,
                "validation": {
                    "min": 18,
                    "max": 120
                }
            }
        ]
    }


def run_interactive_demo():
    """Run an interactive demo of the intake form agent."""
    # Load configuration
    config = AgentConfig(
        default_mode=os.getenv("DEFAULT_MODE", "hybrid"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    set_config(config)
    
    # Create graph
    graph = create_intake_graph()
    
    # Initialize state
    schema = create_sample_schema()
    state = {
        "messages": [],
        "form_schema": schema,
        "current_field_id": schema["fields"][0]["id"],
        "collected_fields": {},
        "validation_result": {},
        "clarification_count": 0,
        "is_complete": False,
        "notes": [],
        "mode": config.default_mode
    }
    
    print("=" * 60)
    print("Dynamic Intake Form Agent - Interactive Demo")
    print("=" * 60)
    print(f"Mode: {config.default_mode}")
    print()
    
    # Run the graph
    max_iterations = 50
    iteration = 0
    
    while not state.get("is_complete") and iteration < max_iterations:
        iteration += 1
        
        # Invoke graph (starts at ask node)
        state = graph.invoke(state)
        
        # Get last AI message
        last_message = None
        for msg in reversed(state.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                last_message = msg
                break
            elif isinstance(msg, dict) and msg.get("type") == "ai":
                last_message = msg
                break
        
        if last_message:
            content = last_message.content if hasattr(last_message, "content") else last_message.get("content", "")
            print(f"Agent: {content}")
        
        # Check if we need user input
        if state.get("is_complete"):
            break
        
        # Get user input
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        
        state["messages"].append(HumanMessage(content=user_input))
    
    # Display results
    print("\n" + "=" * 60)
    print("Form Complete!")
    print("=" * 60)
    print("\nCollected Data:")
    for field_id, data in state.get("collected_fields", {}).items():
        value = data.get("value", "N/A")
        notes = data.get("notes", [])
        print(f"  {field_id}: {value}")
        if notes:
            print(f"    Notes: {', '.join(notes)}")


if __name__ == "__main__":
    run_interactive_demo()

