"""Node implementations for the intake form graph."""

from typing import Dict, Any
from langchain_core.messages import AIMessage

from src.graph import FormState
from src.utils import (
    get_field,
    get_last_user_message,
    get_ordered_fields,
    get_field_index,
    should_show_field,
)
from src.validation import validate_value
from src.modes import (
    ask_speed,
    ask_quality,
    process_speed,
    process_quality,
    clarify_speed,
    clarify_quality,
    annotate_speed,
    annotate_quality,
    verify_quality,
)
from src.config import AgentConfig


# Global config (can be set per graph instance)
_config = AgentConfig()


def set_config(config: AgentConfig):
    """Set global configuration."""
    global _config
    _config = config


def get_mode_for_node(node: str, state: FormState) -> str:
    """Determine mode for a specific node (hybrid mode logic)."""
    if _config.default_mode != "hybrid":
        return _config.default_mode
    
    field = get_field(state.get("current_field_id"), state.get("form_schema", {}))
    if not field:
        return "speed"
    
    # Always use LLM for clarification
    if node == "clarify":
        return "quality"
    
    # Use LLM for complex field types
    if node in ["ask", "process"]:
        field_type = field.get("field_type", "")
        if field_type in _config.complex_field_types:
            if len(field.get("description", "")) > 50:
                return "quality"
    
    # Use LLM if previous extraction had low confidence
    if node == "process":
        prev = state.get("collected_fields", {}).get(state.get("current_field_id"))
        if prev and prev.get("confidence", 1.0) < _config.confidence_threshold:
            return "quality"
    
    # Use LLM for annotation if response is complex
    if node == "annotate":
        collected = state.get("collected_fields", {}).get(state.get("current_field_id"), {})
        raw = collected.get("raw", "")
        if len(raw) > _config.complex_response_length or len(raw.split()) > 20:
            return "quality"
    
    return "speed"


def ask_node(state: FormState) -> FormState:
    """Generate question for current field."""
    field = get_field(state.get("current_field_id"), state.get("form_schema", {}))
    if not field:
        return state
    
    context = state.get("collected_fields", {})
    mode = get_mode_for_node("ask", state)
    
    if mode == "speed":
        question = ask_speed(field, context)
    else:
        question = ask_quality(field, context, _config)
    
    messages = state.get("messages", [])
    messages.append(AIMessage(content=question))
    
    return {**state, "messages": messages}


def process_node(state: FormState) -> FormState:
    """Extract structured value from user input."""
    field = get_field(state.get("current_field_id"), state.get("form_schema", {}))
    if not field:
        return state
    
    user_input = get_last_user_message(state)
    mode = get_mode_for_node("process", state)
    
    if mode == "speed":
        result = process_speed(user_input, field)
    else:
        result = process_quality(user_input, field, _config)
    
    field_id = state.get("current_field_id")
    collected = state.get("collected_fields", {})
    collected[field_id] = result
    
    return {**state, "collected_fields": collected}


def validate_node(state: FormState) -> FormState:
    """Validate extracted value."""
    field = get_field(state.get("current_field_id"), state.get("form_schema", {}))
    if not field:
        return state
    
    field_id = state.get("current_field_id")
    collected = state.get("collected_fields", {}).get(field_id, {})
    
    # Always do rule-based validation
    result = validate_value(collected.get("value"), field)
    
    # Quality mode adds LLM verification
    mode = state.get("mode", _config.default_mode)
    if mode == "quality" and result.get("valid"):
        result = verify_quality(collected, field, result, _config)
    
    return {**state, "validation_result": result}


def clarify_node(state: FormState) -> FormState:
    """Generate clarification request."""
    field = get_field(state.get("current_field_id"), state.get("form_schema", {}))
    if not field:
        return state
    
    errors = state.get("validation_result", {}).get("errors", [])
    field_id = state.get("current_field_id")
    collected = state.get("collected_fields", {}).get(field_id, {})
    attempt = state.get("clarification_count", 0) + 1
    mode = get_mode_for_node("clarify", state)
    
    if mode == "speed":
        message = clarify_speed(field, errors, attempt)
    else:
        message = clarify_quality(field, errors, collected, attempt, _config)
    
    messages = state.get("messages", [])
    messages.append(AIMessage(content=message))
    
    return {
        **state,
        "messages": messages,
        "clarification_count": attempt
    }


def annotate_node(state: FormState) -> FormState:
    """Detect and add notes to collected field."""
    field_id = state.get("current_field_id")
    collected = state.get("collected_fields", {}).get(field_id, {})
    mode = get_mode_for_node("annotate", state)
    
    if mode == "speed":
        notes = annotate_speed(collected.get("raw", ""))
    else:
        notes = annotate_quality(collected, state, _config)
    
    # Merge notes
    existing_notes = collected.get("notes", [])
    collected["notes"] = existing_notes + notes
    
    collected_fields = state.get("collected_fields", {})
    collected_fields[field_id] = collected
    
    return {**state, "collected_fields": collected_fields}


def advance_node(state: FormState) -> FormState:
    """Move to next applicable field."""
    form_schema = state.get("form_schema", {})
    fields = get_ordered_fields(form_schema)
    current_id = state.get("current_field_id")
    current_idx = get_field_index(current_id, fields)
    
    # Find next applicable field
    next_field_id = None
    collected = state.get("collected_fields", {})
    
    for i in range(current_idx + 1, len(fields)):
        field = fields[i]
        if should_show_field(field, collected):
            next_field_id = field.get("id")
            break
    
    return {
        **state,
        "current_field_id": next_field_id,
        "is_complete": next_field_id is None,
        "clarification_count": 0,
        "validation_result": {}
    }


def output_node(state: FormState) -> FormState:
    """Generate final output."""
    # Output is the collected fields
    return state


def route_validation(state: FormState) -> str:
    """Route based on validation result."""
    result = state.get("validation_result", {})
    
    if result.get("valid"):
        return "valid"
    
    # Max clarification attempts
    if state.get("clarification_count", 0) >= _config.max_clarification_attempts:
        # Accept with note
        field_id = state.get("current_field_id")
        collected = state.get("collected_fields", {})
        field_data = collected.get(field_id, {})
        notes = field_data.get("notes", [])
        notes.append("Accepted after max clarification attempts")
        field_data["notes"] = notes
        collected[field_id] = field_data
        state["collected_fields"] = collected
        return "accept_with_note"
    
    return "invalid"


def route_completion(state: FormState) -> str:
    """Route based on completion status."""
    return "complete" if state.get("is_complete") else "continue"

