"""Utility functions for the intake form agent."""

from typing import Dict, Any, Optional


def get_field(field_id: Optional[str], form_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get field definition from schema by ID."""
    if not field_id:
        return None
    
    fields = form_schema.get("fields", [])
    for field in fields:
        if field.get("id") == field_id:
            return field
    return None


def get_ordered_fields(form_schema: Dict[str, Any]) -> list:
    """Get ordered list of fields from schema."""
    return form_schema.get("fields", [])


def get_field_index(field_id: Optional[str], fields: list) -> int:
    """Get index of field in ordered list."""
    if not field_id:
        return -1
    
    for i, field in enumerate(fields):
        if field.get("id") == field_id:
            return i
    return -1


def get_last_user_message(state: Dict[str, Any]) -> str:
    """Extract the last user message from state."""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and hasattr(msg, "type"):
            if msg.type == "human":
                return msg.content
        elif isinstance(msg, dict) and msg.get("type") == "human":
            return msg.get("content", "")
    return ""


def summarize_context(collected_fields: Dict[str, Any]) -> str:
    """Summarize collected fields for context."""
    if not collected_fields:
        return "No previous responses."
    
    summary = []
    for field_id, data in collected_fields.items():
        value = data.get("value", "")
        summary.append(f"{field_id}: {value}")
    
    return "; ".join(summary)


def should_show_field(field: Dict[str, Any], collected: Dict[str, Any]) -> bool:
    """Evaluate conditional display rules."""
    cond = field.get("conditional")
    if not cond:
        return True
    
    depends_on = cond.get("depends_on")
    if not depends_on or depends_on not in collected:
        return False
    
    value = collected[depends_on].get("value")
    target = cond.get("value")
    op = cond.get("condition", "equals")
    
    ops = {
        "equals": lambda v, t: v == t,
        "not_equals": lambda v, t: v != t,
        "contains": lambda v, t: t in str(v),
        "greater_than": lambda v, t: float(v) > float(t),
        "less_than": lambda v, t: float(v) < float(t),
        "in": lambda v, t: v in t if isinstance(t, list) else False,
    }
    
    return ops.get(op, lambda v, t: True)(value, target)

