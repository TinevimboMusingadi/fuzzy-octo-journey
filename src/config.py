"""Configuration for the Intake Form Agent."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AgentConfig:
    """Configuration for the intake form agent."""
    
    # Mode selection
    default_mode: Literal["speed", "quality", "hybrid"] = "hybrid"
    
    # Hybrid mode thresholds
    confidence_threshold: float = 0.7  # Below this, use LLM
    complex_response_length: int = 100  # Above this, use LLM for annotation
    complex_field_types: list = field(default_factory=lambda: ["address", "text"])
    
    # Reliability settings
    max_clarification_attempts: int = 3
    llm_timeout_seconds: float = 5.0
    fallback_on_error: bool = True
    
    # LLM settings
    llm_model: str = "gpt-4o-mini"  # Faster, cheaper for structured tasks
    llm_temperature: float = 0.3    # Lower for consistency

