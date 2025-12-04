"""Helpers for creating and running V2.0 intake sessions.

This module provides a clean API for:
- Selecting a pre-built form by `form_id`
- Creating the initial `FormState`
- Getting back a compiled graph ready to run
"""

from typing import Dict, Any

from src.config import AgentConfig
from src.graph import create_intake_graph
from src.nodes import set_config
from src.v2.forms_registry import get_form_schema


def create_session(form_id: str, mode: str = "hybrid") -> Dict[str, Any]:
    """Create a new intake form session for a specific pre-built form.

    Returns a dict with:
    - graph: compiled LangGraph
    - state: initial FormState values
    - config: AgentConfig used for the session
    """
    schema = get_form_schema(form_id)
    if not schema:
        raise ValueError(f"Unknown form_id: {form_id}")

    config = AgentConfig(default_mode=mode)
    set_config(config)

    graph = create_intake_graph(checkpointer=None)

    fields = schema.get("fields", [])
    if not fields:
        raise ValueError(f"Form schema '{form_id}' has no fields defined")

    initial_state: Dict[str, Any] = {
        "messages": [],
        "form_schema": schema,
        "current_field_id": fields[0]["id"],
        "collected_fields": {},
        "validation_result": {},
        "clarification_count": 0,
        "is_complete": False,
        "notes": [],
        "mode": mode,
    }

    return {
        "graph": graph,
        "state": initial_state,
        "config": config,
    }


