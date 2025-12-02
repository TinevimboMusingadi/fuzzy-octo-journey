"""Enhanced evaluation script for the Dynamic Intake Form Agent."""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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

def load_test_cases(path: str) -> List[TestCase]:
    with open(path, "r") as f:
        data = json.load(f)
    return [TestCase(**item) for item in data]

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

def run_test_case(test_case: TestCase) -> Dict[str, Any]:
    print(f"\nRunning Test Case: {test_case.id}")
    print(f"Description: {test_case.description}")
    print(f"Mode: {test_case.mode}")
    
    # Setup
    config = AgentConfig(default_mode=test_case.mode)
    set_config(config)
    checkpointer = MemorySaver()
    
    # Mock LLM
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
            # print(f"  Input: {user_input}")
            
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
        failures = []
        
        for field_id, expected in test_case.expected_values.items():
            actual = collected.get(field_id, {}).get("value")
            match = str(actual) == str(expected)
            if not match:
                passed = False
                failures.append(f"{field_id}: Expected '{expected}', Got '{actual}'")
        
        status = "PASSED" if passed else "FAILED"
        print(f"  Status: {status} ({duration:.2f}s)")
        if not passed:
            for f in failures:
                print(f"    ❌ {f}")
                
        return {
            "id": test_case.id,
            "passed": passed,
            "duration": duration,
            "failures": failures,
            "collected": collected
        }

def compare_results(current: List[Dict], previous: List[Dict]):
    print("\n=== Regression Report ===")
    prev_map = {r["id"]: r for r in previous}
    
    for curr in current:
        prev = prev_map.get(curr["id"])
        if not prev:
            print(f"🆕 {curr['id']}: New test case")
            continue
            
        if curr["passed"] != prev["passed"]:
            status = "🔴 BROKEN" if prev["passed"] and not curr["passed"] else "🟢 FIXED"
            print(f"{status} {curr['id']}")
        
        # Latency check (warn if > 50% slower)
        if curr["duration"] > prev["duration"] * 1.5:
            print(f"⚠️  {curr['id']}: Latency regression ({prev['duration']:.2f}s -> {curr['duration']:.2f}s)")

def main():
    parser = argparse.ArgumentParser(description="Run intake form agent evaluations")
    parser.add_argument("--mode", choices=["speed", "quality", "hybrid", "all"], default="all", help="Test mode filter")
    parser.add_argument("--save", action="store_true", help="Save results to eval_results.json")
    parser.add_argument("--diff", action="store_true", help="Compare with previous results")
    args = parser.parse_args()
    
    # Load cases
    cases_path = Path(__file__).parent / "data" / "eval_cases.json"
    cases = load_test_cases(str(cases_path))
    
    # Filter cases
    if args.mode != "all":
        cases = [c for c in cases if c.mode == args.mode]
    
    print(f"Running {len(cases)} test cases...")
    results = []
    
    for case in cases:
        try:
            result = run_test_case(case)
            results.append(result)
        except Exception as e:
            print(f"❌ Error running {case.id}: {e}")
            results.append({
                "id": case.id,
                "passed": False,
                "duration": 0,
                "failures": [str(e)],
                "collected": {}
            })
            
    # Summary
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\nSummary: {passed_count}/{len(results)} Passed")
    
    # Diff
    if args.diff:
        results_path = Path("eval_results.json")
        if results_path.exists():
            with open(results_path, "r") as f:
                prev_results = json.load(f)
            compare_results(results, prev_results)
        else:
            print("\n⚠️  No previous results found for diff.")
            
    # Save
    if args.save:
        with open("eval_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("\nResults saved to eval_results.json")
        
    if passed_count < len(results):
        sys.exit(1)

if __name__ == "__main__":
    main()
