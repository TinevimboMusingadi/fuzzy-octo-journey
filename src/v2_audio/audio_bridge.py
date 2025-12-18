"""Bridge between LangGraph agent and Gemini Live API for voice interaction."""

import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from langchain_core.messages import HumanMessage

from src.v2_audio.voice_session import VoiceSession
from src.v2_audio.config import VoiceConfig
from src.v2.session import create_session


class AudioBridge:
    """Bridges text-based LangGraph agent with voice-enabled Live API."""
    
    def __init__(
        self,
        form_id: str,
        mode: str,
        voice_config: VoiceConfig,
        api_key: Optional[str] = None
    ):
        """Initialize audio bridge with form and voice configuration."""
        self.form_id = form_id
        self.mode = mode
        self.voice_config = voice_config
        
        # Create LangGraph session (same as V2.0)
        self.agent_session = create_session(form_id=form_id, mode=mode)
        self.graph = self.agent_session["graph"]
        self.agent_state = self.agent_session["state"]
        self.config_run = {"configurable": {"thread_id": f"voice_{form_id}"}}
        
        # Create Live API voice session
        self.voice_session = VoiceSession(voice_config, api_key=api_key)
        
        # Callbacks for audio events
        self.on_audio_output: Optional[Callable[[bytes], Awaitable[None]]] = None
        self.on_transcription: Optional[Callable[[str, str], Awaitable[None]]] = None
        self.on_agent_text: Optional[Callable[[str], Awaitable[None]]] = None
    
    async def initialize(self):
        """Initialize both agent and voice session."""
        # Connect to Live API
        await self.voice_session.connect()
        
        # Run agent to get first question
        await self._run_agent_until_question()
    
    async def _run_agent_until_question(self):
        """Run agent graph until we get a question (ask node)."""
        # Stream agent execution
        for _ in self.graph.stream(self.agent_state, self.config_run):
            pass
        
        # Get current state
        current_state = self.graph.get_state(self.config_run)
        self.agent_state = current_state.values
        
        # Extract last AI message (the question)
        messages = self.agent_state.get("messages", [])
        question = None
        
        for msg in reversed(messages):
            msg_type = getattr(msg, "type", None) or getattr(msg, "role", None) or msg.__dict__.get("type")
            if msg_type == "ai":
                question = getattr(msg, "content", "") or getattr(msg, "text", "")
                break
        
        if question:
            # Notify callback with text (always show text even if audio fails)
            if self.on_agent_text:
                await self.on_agent_text(question)
            
            # Try to send to Live API for audio output
            # Note: Live API is conversational, so we ask it to speak our question
            try:
                await self.voice_session.send_text(question, turn_complete=True)
                
                # Listen for audio output from Live API (with timeout per message)
                import asyncio
                timeout = 15.0  # Give more time for audio response
                start_time = asyncio.get_event_loop().time()
                
                try:
                    response_count = 0
                    async for response in self.voice_session.receive():
                        response_count += 1
                        
                        # Check timeout
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed > timeout:
                            # Only break if we've been waiting a long time
                            break
                        
                        response_type = response.get("type", "unknown")
                        
                        # Debug: Show what we're receiving
                        if response_type != "unknown":
                            print(f"📥 Received: {response_type}", end="", flush=True)
                        
                        if response_type == "audio_output":
                            # Play audio
                            audio_data = response.get("audio")
                            if audio_data and len(audio_data) > 0:
                                if self.on_audio_output:
                                    await self.on_audio_output(audio_data)
                                print(" ✅")
                            else:
                                print(" ⚠️  (no audio data)")
                        elif response_type == "output_transcription":
                            # Show transcription word-by-word (like the original working version)
                            transcription_text = response.get("text", "")
                            if transcription_text and self.on_transcription:
                                await self.on_transcription("output", transcription_text)
                            print(" (transcription)")
                        elif response_type == "interrupted":
                            # User interrupted
                            print(" (interrupted)")
                            break
                        else:
                            print(f" (type: {response_type})")
                        
                        # Don't break immediately - let Live API finish speaking
                        # Only break on timeout or interruption
                        # We'll let the timeout handle ending the audio stream
                    
                    if response_count == 0:
                        print("⚠️  No responses received from Live API")
                except Exception as e:
                    print(f"\n⚠️  Error receiving from Live API: {e}")
                    import traceback
                    traceback.print_exc()
                except Exception as e:
                    print(f"⚠️  Error receiving from Live API: {e}")
            except Exception as e:
                print(f"⚠️  Error sending to Live API: {e}")
                print("   Continuing with text-only mode...")
    
    async def process_user_input(self, user_text: str):
        """Process user text input through agent and get response."""
        # Add user message to agent state
        self.graph.update_state(
            self.config_run,
            {"messages": [HumanMessage(content=user_text)]},
        )
        
        # Run agent to process and get next question
        await self._run_agent_until_question()
    
    async def process_user_audio(self, audio_data: bytes):
        """Process user audio: send to Live API for transcription, then to agent."""
        # Send audio to Live API
        await self.voice_session.send_audio(audio_data, self.voice_config.input_sample_rate)
        
        # Wait for transcription
        async for response in self.voice_session.receive():
            if response["type"] == "input_transcription":
                user_text = response["text"]
                
                # Notify transcription callback
                if self.on_transcription:
                    await self.on_transcription("input", user_text)
                
                # Process through agent
                await self.process_user_input(user_text)
                break
    
    async def listen_and_process(self):
        """Main loop: listen for Live API responses and process them."""
        async for response in self.voice_session.receive():
            response_type = response["type"]
            
            if response_type == "input_transcription":
                # User spoke - process through agent
                user_text = response["text"]
                
                if self.on_transcription:
                    await self.on_transcription("input", user_text)
                
                await self.process_user_input(user_text)
            
            elif response_type == "audio_output":
                # Agent audio response - play it
                audio_data = response["audio"]
                
                if self.on_audio_output:
                    await self.on_audio_output(audio_data)
            
            elif response_type == "output_transcription":
                # Agent speech transcription
                agent_text = response["text"]
                
                if self.on_transcription:
                    await self.on_transcription("output", agent_text)
            
            elif response_type == "interrupted":
                # User interrupted agent
                if self.on_transcription:
                    await self.on_transcription("system", "User interrupted agent")
            
            # Check if form is complete
            if self.agent_state.get("is_complete"):
                break
    
    def get_collected_data(self) -> Dict[str, Any]:
        """Get collected form data from agent."""
        return self.agent_state.get("collected_fields", {})
    
    def is_complete(self) -> bool:
        """Check if form is complete."""
        return self.agent_state.get("is_complete", False)
    
    async def close(self):
        """Close voice session."""
        await self.voice_session.close()

