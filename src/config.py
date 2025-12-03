"""Configuration for the Intake Form Agent."""

from dataclasses import dataclass, field
from typing import Literal, Optional


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
"""Configuration for the Intake Form Agent."""

from dataclasses import dataclass, field
from typing import Literal, Optional


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
    # Available Gemini models: gemini-2.5-pro, gemini-2.5-flash, gemini-3-pro-preview
    llm_model: str = "gemini-2.5-pro"  # Universal model (works with all API keys)
    llm_temperature: float = 0.3    # Lower for consistency
    llm_provider: Literal["google", "openai"] = "google"  # API provider
    google_api_key: Optional[str] = None  # Will use GOOGLE_API_KEY env var if None

