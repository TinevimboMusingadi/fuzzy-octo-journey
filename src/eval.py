"""Evaluation script for the Dynamic Intake Form Agent."""

import sys
from pathlib import Path

# Add project root to path
if Path(__file__).parent.name == "src":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import time
import asyncio
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from src.graph import create_intake_graph
from src.nodes import set_config
from src.config import AgentConfig

@dataclass
class TestCase:
    id: str
    description: str
    inputs: List[str]
    expected_values: Dict[str, Any]
    mode: str = "hybrid"

TEST_CASES = [
    TestCase(
        id="simple_happy_path",
        description="Simple inputs, no clarification needed",
        inputs=[
            "John Doe",
            "john@example.com",
            "555-123-4567",
            "25"
        ],
        expected_values={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "(555) 123-4567",
            "age": 25.0
        },
        mode="speed"
    ),
    TestCase(
        id="complex_input_quality",
        description="Complex inputs requiring LLM extraction",
        inputs=[
            "My name is Sarah Connor",
            "You can reach me at sarah.connor@skynet.com",
            "Call me at 555-987-6543",
            "I am thirty years old"
        ],
        expected_values={
            "name": "Sarah Connor",
            "email": "sarah.connor@skynet.com",
            "phone": "(555) 987-6543",
            "age": 30.0
        },
        mode="quality"
    )
]

def create_test_schema():
    return {
        "fields": [
            {
                "id": "name",
                "field_type": "text",
                "label": "Full Name",
                "required": True
            },
            {
                "id": "email",
                "field_type": "email",
                "label": "Email Address",
                "required": True
            },
            {
                "id": "phone",
                "field_type": "phone",
                "label": "Phone Number",
                "required": False
            },
            {
                "id": "age",
                "field_type": "number",
                "label": "Age",
                "required": False
            }
        ]
    }

from unittest.mock import MagicMock, patch

def mock_llm_response(prompt):
    content = prompt[0].content
    if "Generate a natural, conversational question" in content:
        if "Full Name" in content: return "What is your full name?"
        if "Email Address" in content: return "What is your email address?"
        if "Phone Number" in content: return "What is your phone number?"
        if "Age" in content: return "How old are you?"
    
    if "Extract the" in content:
        if "Sarah Connor" in content: return json.dumps({"value": "Sarah Connor", "confidence": 0.95})
        if "sarah.connor@skynet.com" in content: return json.dumps({"value": "sarah.connor@skynet.com", "confidence": 0.95})
        if "555-987-6543" in content: return json.dumps({"value": "(555) 987-6543", "confidence": 0.95})
        if "thirty years old" in content: return json.dumps({"value": 30.0, "confidence": 0.95})
        
    if "Verify this extracted value" in content:
        return json.dumps({"valid": True, "needs_clarification": False})
        
    if "Analyze this response" in content:
        return json.dumps([])
        
    return "I don't know"

def run_test_case(test_case: TestCase):
    print(f"\nRunning Test Case: {test_case.id}")
    print(f"Description: {test_case.description}")
    print(f"Mode: {test_case.mode}")
    
    # Setup
    config = AgentConfig(default_mode=test_case.mode)
    set_config(config)
    checkpointer = MemorySaver()
    
    # Mock LLM if in quality mode
    with patch('src.modes.get_llm') as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = lambda x: MagicMock(content=mock_llm_response(x))
        mock_get_llm.return_value = mock_llm
        
        graph = create_intake_graph(checkpointer=checkpointer)
        
        schema = create_test_schema()
        initial_state = {
            "messages": [],
            "form_schema": schema,
            "current_field_id": schema["fields"][0]["id"],
            "collected_fields": {},
            "validation_result": {},
            "clarification_count": 0,
            "is_complete": False,
            "notes": [],
            "mode": test_case.mode
        }
        
        thread_id = f"test_{test_case.id}"
        config_run = {"configurable": {"thread_id": thread_id}}
        
        start_time = time.time()
        
        # Initial run
        for event in graph.stream(initial_state, config_run):
            pass
        
        current_state = graph.get_state(config_run)
        input_idx = 0
        
        while not current_state.values.get("is_complete") and input_idx < len(test_case.inputs):
            user_input = test_case.inputs[input_idx]
            print(f"  Input: {user_input}")
            
            graph.update_state(
                config_run,
                {"messages": [HumanMessage(content=user_input)]},
            )
            
            for event in graph.stream(None, config_run):
                pass
                
            current_state = graph.get_state(config_run)
            input_idx += 1
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify results
        collected = current_state.values.get("collected_fields", {})
        passed = True
        
        print("  Results:")
        for field_id, expected in test_case.expected_values.items():
            actual = collected.get(field_id, {}).get("value")
            match = str(actual) == str(expected)
            status = "✅" if match else "❌"
            if not match:
                passed = False
            print(f"    {status} {field_id}: Expected '{expected}', Got '{actual}'")
            
        print(f"  Duration: {duration:.2f}s")
        print(f"  Status: {'PASSED' if passed else 'FAILED'}")
        return passed

if __name__ == "__main__":
    print("Starting Evaluation...")
    results = []
    for test_case in TEST_CASES:
        try:
            passed = run_test_case(test_case)
            results.append(passed)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append(False)
            
    print("\nSummary:")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
