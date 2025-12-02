"""Main entry point for the intake form agent."""

import os
import sys
from pathlib import Path

# Add project root to path if running from src directory
if Path(__file__).parent.name == "src":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

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
    # Available Gemini models: gemini-1.5-pro, gemini-1.5-flash, gemini-3-pro-preview
    config = AgentConfig(
        default_mode=os.getenv("DEFAULT_MODE", "hybrid"),
        llm_model=os.getenv("LLM_MODEL", "gemini-3-pro-preview"),
        llm_provider=os.getenv("LLM_PROVIDER", "google"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        fallback_on_error=True  # Always fallback to speed mode on LLM errors
    )
    set_config(config)
    
    # Initialize checkpointer
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    # Create graph with checkpointer
    graph = create_intake_graph(checkpointer=checkpointer)
    
    # Initialize state
    schema = create_sample_schema()
    initial_state = {
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
    thread_id = "demo_thread"
    config_run = {"configurable": {"thread_id": thread_id}}
    
    # Start the graph
    # We use stream to get updates, but we could also use invoke
    # Since we have an interrupt, invoke will stop at the interrupt
    
    # First run to get to the first question
    for event in graph.stream(initial_state, config_run):
        pass
        
    # Get the current state
    current_state = graph.get_state(config_run)
    
    while True:
        # Check if we are done
        if not current_state.next:
            # If no next steps and we are done, break
            if current_state.values.get("is_complete"):
                break
            # If no next steps but not complete, something is wrong, but let's break to avoid infinite loop
            if not current_state.next:
                break

        # Get the last message (the question)
        messages = current_state.values.get("messages", [])
        last_message = None
        for msg in reversed(messages):
            if hasattr(msg, "type") and msg.type == "ai":
                last_message = msg
                break
            elif isinstance(msg, dict) and msg.get("type") == "ai":
                last_message = msg
                break
        
        if last_message:
            content = last_message.content if hasattr(last_message, "content") else last_message.get("content", "")
            print(f"Agent: {content}")
        
        # Get user input
        try:
            user_input = input("\nYou: ").strip()
        except EOFError:
            break
            
        if not user_input:
            continue
            
        # Update state with user input and resume
        # We need to add the human message to the state
        # The 'process' node expects the last message to be the user's answer
        
        # Resume the graph
        # We update the state with the new message
        graph.update_state(
            config_run,
            {"messages": [HumanMessage(content=user_input)]},
        )
        
        # Continue execution
        for event in graph.stream(None, config_run):
            pass
            
        # Update current state for next iteration
        current_state = graph.get_state(config_run)
    
    # Display results
    print("\n" + "=" * 60)
    print("Form Complete!")
    print("=" * 60)
    print("\nCollected Data:")
    print("\nCollected Data:")
    final_state = graph.get_state(config_run).values
    for field_id, data in final_state.get("collected_fields", {}).items():
        value = data.get("value", "N/A")
        notes = data.get("notes", [])
        print(f"  {field_id}: {value}")
        if notes:
            print(f"    Notes: {', '.join(notes)}")


if __name__ == "__main__":
    run_interactive_demo()

