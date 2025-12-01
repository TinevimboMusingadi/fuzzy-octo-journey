"""Type definitions for the intake form agent."""

from typing import TypedDict, Literal, Optional, Any
from langchain_core.messages import BaseMessage


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

