"""CLI entry point for V2 Audio voice-enabled form filling.

Example usage:
    python -m src.main_v2_audio --form-id employment_onboarding --mode quality
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Add project root to path
if Path(__file__).parent.name == "src":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.v2_audio.audio_bridge import AudioBridge
from src.v2_audio.config import VoiceConfig, get_voice_config_from_env
from src.v2_audio.audio_utils import AudioCapture, AudioPlayback, list_audio_devices
from src.output_handlers import JSONOutputHandler, CSVOutputHandler

# Load environment variables
load_dotenv()


async def run_voice_cli(form_id: str, mode: str, voice_config: VoiceConfig):
    """Run interactive voice-based form filling."""
    print("=" * 60)
    print(f"Voice-Enabled Intake Form Agent - V2 Audio ({form_id})")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Voice: {voice_config.voice_name}")
    print(f"Model: {voice_config.model}")
    print()
    
    # Get API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY not found in environment")
        print("   Please set it in .env file or environment variable")
        return
    
    # Check if pyaudio is available
    try:
        import pyaudio
    except ImportError:
        print("❌ ERROR: pyaudio is required for voice mode")
        print("   Install with: pip install pyaudio")
        print("   On Windows, you may need: pip install pipwin && pipwin install pyaudio")
        return
    
    # List audio devices
    print("📢 Available Audio Devices:")
    devices = list_audio_devices()
    if devices:
        for dev in devices[:5]:  # Show first 5
            print(f"  [{dev['index']}] {dev['name']} "
                  f"(in: {dev['channels_in']}, out: {dev['channels_out']})")
    print()
    
    # Initialize audio bridge
    print("🔌 Connecting to Gemini Live API...")
    bridge = AudioBridge(
        form_id=form_id,
        mode=mode,
        voice_config=voice_config,
        api_key=api_key
    )
    
    # Set up callbacks
    audio_capture = AudioCapture(
        sample_rate=voice_config.input_sample_rate,
        device_index=None  # Use default device
    )
    
    audio_playback = AudioPlayback(
        sample_rate=voice_config.output_sample_rate,
        device_index=None  # Use default device
    )
    
    # Transcription display callback
    async def on_transcription(source: str, text: str):
        if source == "input":
            print(f"👤 You: {text}")
        elif source == "output":
            print(f"🤖 Agent: {text}")
        elif source == "system":
            print(f"ℹ️  {text}")
    
    # Audio output callback
    async def on_audio_output(audio_data: bytes):
        await audio_playback.play_async(audio_data)
    
    # Agent text callback
    async def on_agent_text(text: str):
        print(f"🤖 Agent: {text}")
    
    bridge.on_transcription = on_transcription
    bridge.on_audio_output = on_audio_output
    bridge.on_agent_text = on_agent_text
    
    try:
        # Start audio I/O
        print("🎤 Starting microphone...")
        audio_capture.start()
        
        print("🔊 Starting speaker...")
        audio_playback.start()
        
        # Initialize bridge (connects to Live API and gets first question)
        print("🚀 Initializing voice session...")
        await bridge.initialize()
        
        print("\n" + "=" * 60)
        print("🎙️  Voice session active! Speak your answers.")
        print("   Say 'quit' or 'exit' to end the session")
        print("=" * 60 + "\n")
        
        # Main conversation loop
        while not bridge.is_complete():
            # Stream audio from microphone to Live API
            audio_chunk = await audio_capture.read_async()
            if audio_chunk:
                await bridge.voice_session.send_audio(
                    audio_chunk,
                    voice_config.input_sample_rate
                )
            
            # Process Live API responses
            try:
                response = await asyncio.wait_for(
                    bridge.voice_session.receive().__anext__(),
                    timeout=0.1
                )
                
                response_type = response.get("type")
                
                if response_type == "input_transcription":
                    # User spoke - process through agent
                    user_text = response["text"]
                    await bridge.process_user_input(user_text)
                
                elif response_type == "audio_output":
                    # Agent audio - play it
                    audio_data = response["audio"]
                    await audio_playback.play_async(audio_data)
                
                elif response_type == "interrupted":
                    print("⚠️  You interrupted the agent")
            
            except asyncio.TimeoutError:
                # No response yet, continue
                pass
            except StopAsyncIteration:
                # End of stream
                break
        
        # Form complete
        print("\n" + "=" * 60)
        print("✅ Form Complete!")
        print("=" * 60)
        
        collected = bridge.get_collected_data()
        print("\n📋 Collected Data:")
        for field_id, data in collected.items():
            value = data.get("value", "N/A")
            print(f"  {field_id}: {value}")
        
        # Save data
        print("\n💾 Saving data...")
        json_handler = JSONOutputHandler()
        json_path = json_handler.save(collected, metadata={
            "mode": mode,
            "form_id": form_id,
            "voice_mode": True,
            "voice_name": voice_config.voice_name,
        })
        print(f"✅ Saved to JSON: {json_path}")
        
        csv_handler = CSVOutputHandler()
        csv_path = csv_handler.save(collected)
        print(f"✅ Appended to CSV: {csv_path}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await bridge.close()
        audio_capture.close()
        audio_playback.close()
        print("✅ Done")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run voice-enabled intake form agent"
    )
    parser.add_argument(
        "--form-id",
        required=True,
        help="Form ID (e.g., employment_onboarding, rental_application)",
    )
    parser.add_argument(
        "--mode",
        choices=["speed", "quality", "hybrid"],
        default="hybrid",
        help="Agent mode",
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="Voice name (e.g., Kore, Charon, Fenrir). Default: from env or Kore",
    )
    parser.add_arg