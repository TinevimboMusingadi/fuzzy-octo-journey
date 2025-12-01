"""Tests for node implementations."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage
from src.nodes import (
    ask_node,
    process_node,
    validate_node,
    clarify_node,
    annotate_node,
    advance_node,
    route_validation,
    route_completion,
    set_config,
)
from src.types import FormState
from src.config import AgentConfig


@pytest.fixture
def sample_schema():
    return {
        "fields": [
            {"id": "name", "field_type": "text", "label": "Name", "required": True},
            {"id": "email", "field_type": "email", "label": "Email", "required": True},
            {"id": "age", "field_type": "number", "label": "Age", "required": False}
        ]
    }


@pytest.fixture
def initial_state(sample_schema):
    return {
        "messages": [],
        "form_schema": sample_schema,
        "current_field_id": "name",
        "collected_fields": {},
        "validation_result": {},
        "clarification_count": 0,
        "is_complete": False,
        "notes": [],
        "mode": "speed"
    }


class TestAskNode:
    def test_ask_node_generates_question(self, initial_state):
        state = ask_node(initial_state)
        assert len(state["messages"]) > 0
        last_message = state["messages"][-1]
        assert isinstance(last_message, AIMessage)
        assert len(last_message.content) > 0
    
    def test_ask_node_includes_field_label(self, initial_state):
        state = ask_node(initial_state)
        last_message = state["messages"][-1]
        assert "Name" in last_message.content


class TestProcessNode:
    def test_process_node_extracts_value(self, initial_state):
        initial_state["messages"].append(HumanMessage(content="John Doe"))
        state = process_node(initial_state)
        assert "name" in state["collected_fields"]
        assert "value" in state["collected_fields"]["name"]
    
    def test_process_node_preserves_raw_input(self, initial_state):
        user_input = "John Doe"
        initial_state["messages"].append(HumanMessage(content=user_input))
        state = process_node(initial_state)
        assert state["collected_fields"]["name"]["raw"] == user_input


class TestValidateNode:
    def test_validate_node_valid_value(self, initial_state):
        initial_state["collected_fields"] = {
            "name": {"value": "John Doe", "raw": "John Doe"}
        }
        state = validate_node(initial_state)
        assert "validation_result" in state
        assert state["validation_result"]["valid"] is True
    
    def test_validate_node_invalid_email(self, initial_state):
        initial_state["current_field_id"] = "email"
        initial_state["collected_fields"] = {
            "email": {"value": "not-an-email", "raw": "not-an-email"}
        }
        state = validate_node(initial_state)
        assert state["validation_result"]["valid"] is False
        assert len(state["validation_result"]["errors"]) > 0


class TestClarifyNode:
    def test_clarify_node_generates_message(self, initial_state):
        # Use speed mode to avoid API key requirement
        initial_state["mode"] = "speed"
        initial_state["validation_result"] = {
            "valid": False,
            "errors": ["This field is required"]
        }
        state = clarify_node(initial_state)
        assert len(state["messages"]) > 0
        assert state["clarification_count"] == 1
    
    def test_clarify_node_increments_count(self, initial_state):
        # Use speed mode to avoid API key requirement
        initial_state["mode"] = "speed"
        initial_state["validation_result"] = {
            "valid": False,
            "errors": ["Invalid"]
        }
        initial_state["clarification_count"] = 1
        state = clarify_node(initial_state)
        assert state["clarification_count"] == 2


class TestAnnotateNode:
    def test_annotate_node_adds_notes(self, initial_state):
        initial_state["collected_fields"] = {
            "name": {
                "value": "John",
                "raw": "I think it's John",
                "notes": []
            }
        }
        state = annotate_node(initial_state)
        notes = state["collected_fields"]["name"]["notes"]
        assert len(notes) > 0


class TestAdvanceNode:
    def test_advance_node_moves_to_next_field(self, initial_state, sample_schema):
        initial_state["collected_fields"] = {
            "name": {"value": "John"}
        }
        state = advance_node(initial_state)
        assert state["current_field_id"] == "email"
        assert state["clarification_count"] == 0
    
    def test_advance_node_sets_complete(self, initial_state, sample_schema):
        initial_state["current_field_id"] = "age"
        initial_state["collected_fields"] = {
            "name": {"value": "John"},
            "email": {"value": "john@example.com"},
            "age": {"value": 30}
        }
        state = advance_node(initial_state)
        assert state["is_complete"] is True
        assert state["current_field_id"] is None


class TestRouteValidation:
    def test_route_validation_valid(self, initial_state):
        initial_state["validation_result"] = {"valid": True}
        result = route_validation(initial_state)
        assert result == "valid"
    
    def test_route_validation_invalid(self, initial_state):
        initial_state["validation_result"] = {"valid": False}
        initial_state["clarification_count"] = 0
        result = route_validation(initial_state)
        assert result == "invalid"
    
    def test_route_validation_max_attempts(self, initial_state):
        initial_state["validation_result"] = {"valid": False}
        initial_state["clarification_count"] = 3
        initial_state["collected_fields"] = {
            "name": {"value": "test", "notes": []}
        }
        result = route_validation(initial_state)
        assert result == "accept_with_note"
        assert "max clarification attempts" in initial_state["collected_fields"]["name"]["notes"][0].lower()


class TestRouteCompletion:
    def test_route_completion_complete(self, initial_state):
        initial_state["is_complete"] = True
        result = route_completion(initial_state)
        assert result == "complete"
    
    def test_route_completion_continue(self, initial_state):
        initial_state["is_complete"] = False
        result = route_completion(initial_state)
        assert result == "continue"

