"""Gemini Live API session management for voice-enabled forms."""

import asyncio
from typing import Optional, AsyncIterator, Dict, Any

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None
    print(
        "⚠️  WARNING: google-genai package not found.\n"
        "   Install with: pip install google-genai\n"
        "   Or: pip install -r requirements.txt"
    )

from src.v2_audio.config import VoiceConfig


class VoiceSession:
    """Manages a Gemini Live API session for voice interaction."""
    
    def __init__(self, config: VoiceConfig, api_key: Optional[str] = None):
        """Initialize voice session with configuration."""
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package is required for voice features.\n"
                "Install with: pip install google-genai"
            )
        
        self.config = config
        self.client = genai.Client(api_key=api_key)
        
        # Use v1alpha API version for advanced features
        if config.enable_affective_dialog or config.enable_proactive_audio:
            self.client = genai.Client(
                api_key=api_key,
                http_options={"api_version": "v1alpha"}
            )
        
        self.session: Optional[Any] = None
        self._setup_config = self._build_config()
    
    def _build_config(self) -> types.LiveConnectConfig:
        """Build Live API configuration from VoiceConfig."""
        config_dict: Dict[str, Any] = {
            "response_modalities": [self.config.response_modality],
        }
        
        # Voice configuration
        if self.config.response_modality == "AUDIO":
            config_dict["speech_config"] = {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": self.config.voice_name}
                }
            }
        
        # Transcription
        if self.config.enable_input_transcription:
            config_dict["input_audio_transcription"] = {}
        
        if self.config.enable_output_transcription:
            config_dict["output_audio_transcription"] = {}
        
        # Advanced features
        if self.config.enable_affective_dialog:
            config_dict["enable_affective_dialog"] = True
        
        if self.config.enable_proactive_audio:
            config_dict["proactivity"] = {"proactive_audio": True}
        
        if self.config.enable_thinking:
            config_dict["thinking_config"] = types.ThinkingConfig(
                thinking_budget=self.config.thinking_budget,
                include_thoughts=True
            )
        
        # Voice Activity Detection
        if self.config.vad_enabled:
            config_dict["realtime_input_config"] = {
                "automatic_activity_detection": {
                    "disabled": False,
                    "start_of_speech_sensitivity": getattr(
                        types.StartSensitivity,
                        self.config.start_sensitivity,
                        types.StartSensitivity.START_SENSITIVITY_LOW
                    ),
                    "end_of_speech_sensitivity": getattr(
                        types.EndSensitivity,
                        self.config.end_sensitivity,
                        types.EndSensitivity.END_SENSITIVITY_LOW
                    ),
                    "silence_duration_ms": self.config.silence_duration_ms,
                }
            }
        
        return types.LiveConnectConfig(**config_dict)
    
    async def connect(self):
        """Establish connection to Gemini Live API."""
        # connect() returns an async context manager, so we need to enter it
        context_manager = self.client.aio.live.connect(
            model=self.config.model,
            config=self._setup_config
        )
        self.session = await context_manager.__aenter__()
        self._context_manager = context_manager  # Store for cleanup
        return self.session
    
    async def send_text(self, text: str, turn_complete: bool = True):
        """Send text message to Live API (will be converted to audio if AUDIO mode).
        
        For agent questions, we send it in a way that prompts the model to speak it.
        """
        if not self.session:
            raise RuntimeError("Session not connected. Call connect() first.")
        
        # Send the text as a user message asking the model to say it
        # This is a workaround since Live API doesn't have direct TTS
        prompt = f"Please ask the user this question exactly as written: {text}"
        
        await self.session.send_client_content(
            turns={"role": "user", "parts": [{"text": prompt}]},
            turn_complete=turn_complete
        )
    
    async def send_audio(self, audio_data: bytes, sample_rate: int = 16000):
        """Send raw audio data to Live API."""
        if not self.session:
            raise RuntimeError("Session not connected. Call connect() first.")
        
        await self.session.send_realtime_input(
            audio=types.Blob(
                data=audio_data,
                mime_type=f"audio/pcm;rate={sample_rate}"
            )
        )
    
    async def receive(self) -> AsyncIterator[Dict[str, Any]]:
        """Receive responses from Live API."""
        if not self.session:
            raise RuntimeError("Session not connected. Call connect() first.")
        
        async for response in self.session.receive():
            result = {
                "type": "unknown",
                "data": response,
            }
            
            # Check for audio output
            if hasattr(response, "server_content") and response.server_content:
                sc = response.server_content
                
                # Audio output - check multiple possible locations
                audio_found = False
                
                # Method 1: Check model_turn.parts
                if hasattr(sc, "model_turn") and sc.model_turn:
                    if hasattr(sc.model_turn, "parts"):
                        for part in sc.model_turn.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                result["type"] = "audio_output"
                                result["audio"] = part.inline_data.data
                                result["mime_type"] = getattr(part.inline_data, "mime_type", "audio/pcm")
                                audio_found = True
                                break
                
                # Method 2: Check if there's direct audio data
                if not audio_found and hasattr(sc, "model_turn"):
                    # Try to get audio from model_turn directly
                    model_turn = sc.model_turn
                    if hasattr(model_turn, "parts"):
                        for part in model_turn.parts:
                            # Check for different audio formats
                            if hasattr(part, "inline_data"):
                                inline_data = part.inline_data
                                if inline_data and hasattr(inline_data, "data"):
                                    result["type"] = "audio_output"
                                    result["audio"] = inline_data.data
                                    result["mime_type"] = getattr(inline_data, "mime_type", "audio/pcm")
                                    audio_found = True
                                    break
                
                # Input transcription (user speech)
                if hasattr(sc, "input_transcription") and sc.input_transcription:
                    result["type"] = "input_transcription"
                    result["text"] = sc.input_transcription.text
                
                # Output transcription (agent speech)
                if hasattr(sc, "output_transcription") and sc.output_transcription:
                    result["type"] = "output_transcription"
                    result["text"] = sc.output_transcription.text
                
                # Interruption
                if hasattr(sc, "interrupted") and sc.interrupted:
                    result["type"] = "interrupted"
            
            # Usage metadata
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                result["type"] = "usage"
                result["usage"] = response.usage_metadata
            
            yield result
    
    async def close(self):
        """Close the Live API session."""
        if self.session and hasattr(self, '_context_manager'):
            await self._context_manager.__aexit__(None, None, None)
            self.session = None
            self._context_manager = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

