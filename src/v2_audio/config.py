"""Configuration for V2 Audio voice-enabled forms."""

from dataclasses import dataclass
from typing import Literal, Optional
import os


@dataclass
class VoiceConfig:
    """Configuration for Gemini Live API voice features."""
    
    # Model selection
    model: str = "gemini-2.5-flash-native-audio-preview-09-2025"
    
    # Response modality (AUDIO or TEXT)
    response_modality: Literal["AUDIO", "TEXT"] = "AUDIO"
    
    # Voice selection (see Gemini TTS voices)
    voice_name: str = "Kore"  # Options: Kore, Charon, Fenrir, etc.
    
    # Audio transcription
    enable_input_transcription: bool = True   # Transcribe user speech
    enable_output_transcription: bool = True  # Transcribe agent speech
    
    # Advanced features
    enable_affective_dialog: bool = True      # Emotion-aware responses
    enable_proactive_audio: bool = False      # Agent decides when to respond
    enable_thinking: bool = True              # Show thinking process
    thinking_budget: int = 1024               # Thinking tokens
    
    # Voice Activity Detection
    vad_enabled: bool = True
    start_sensitivity: str = "START_SENSITIVITY_LOW"
    end_sensitivity: str = "END_SENSITIVITY_LOW"
    silence_duration_ms: int = 100
    
    # Audio format
    input_sample_rate: int = 16000  # Hz
    output_sample_rate: int = 24000  # Hz (Live API default)
    
    # API version (for advanced features)
    api_version: str = "v1alpha"  # Required for affective dialog, proactive audio


@dataclass
class AudioIOConfig:
    """Configuration for local audio input/output."""
    
    # Microphone settings
    input_device_index: Optional[int] = None  # None = default device
    input_channels: int = 1  # Mono
    input_chunk_size: int = 1024  # Audio buffer size
    
    # Speaker settings
    output_device_index: Optional[int] = None
    output_channels: int = 1
    
    # Audio processing
    enable_echo_cancellation: bool = True
    enable_noise_suppression: bool = True


def get_voice_config_from_env() -> VoiceConfig:
    """Load voice configuration from environment variables."""
    return VoiceConfig(
        model=os.getenv("LIVE_API_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
        voice_name=os.getenv("VOICE_NAME", "Kore"),
        enable_affective_dialog=os.getenv("ENABLE_AFFECTIVE_DIALOG", "true").lower() == "true",
        enable_proactive_audio=os.getenv("ENABLE_PROACTIVE_AUDIO", "false").lower() == "true",
        enable_thinking=os.getenv("ENABLE_THINKING", "true").lower() == "true",
        thinking_budget=int(os.getenv("THINKING_BUDGET", "1024")),
    )

