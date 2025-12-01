"""LangGraph definition for the intake form agent."""

from typing import TypedDict, Literal, Optional, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from src.nodes import (
    ask_node,
    process_node,
    validate_node,
    clarify_node,
    annotate_node,
    advance_node,
    output_node,
    route_validation,
    route_completion,
)


class FormState(TypedDict):
    """State schema for the intake form graph."""
    messages: list[BaseMessage]
    form_schema: dict[str, Any]
    current_field_id: Optional[str]
    collected_fields: dict[str, Any]
    validation_result: dict[str, Any]
    clarification_count: int
    is_complete: bool
    notes: list[str]
    mode: Literal["speed", "quality"]


def create_intake_graph():
    """Create and compile the intake form LangGraph."""
    graph = StateGraph(FormState)
    
    # Add nodes
    graph.add_node("ask", ask_node)
    graph.add_node("process", process_node)
    graph.add_node("validate", validate_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("annotate", annotate_node)
    graph.add_node("advance", advance_node)
    graph.add_node("output", output_node)
    
    # Define edges
    graph.set_entry_point("ask")
    graph.add_edge("ask", "process")
    graph.add_edge("process", "validate")
    
    graph.add_conditional_edges(
        "validate",
        route_validation,
        {
            "valid": "annotate",
            "invalid": "clarify",
            "accept_with_note": "annotate"
        }
    )
    
    graph.add_edge("clarify", "process")
    graph.add_edge("annotate", "advance")
    
    graph.add_conditional_edges(
        "advance",
        route_completion,
        {
            "continue": "ask",
            "complete": "output"
        }
    )
    
    graph.add_edge("output", END)
    
    return graph.compile()

