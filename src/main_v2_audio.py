"""CLI entry point for V2 Audio voice-enabled form filling.

Example usage:
    python -m src.main_v2_audio --form-id employment_onboarding --mode quality
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
if Path(__file__).parent.name == "src":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

load_dotenv()

from src.v2_audio.audio_bridge import AudioBridge
from src.v2_audio.config import VoiceConfig, AudioIOConfig, get_voice_config_from_env
from src.v2_audio.audio_utils import AudioCapture, AudioPlayback, list_audio_devices


async def run_voice_cli(form_id: str, mode: str, voice_config: VoiceConfig):
    """Run interactive voice-based form filling."""
    print("=" * 60)
    print(f"🎤 Voice-Enabled Intake Form Agent - V2 Audio")
    print("=" * 60)
    print(f"Form: {form_id}")
    print(f"Mode: {mode}")
    print(f"Voice: {voice_config.voice_name}")
    print()
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY not found in environment")
        print("   Please set it in .env file or environment variable")
        return
    
    # Initialize audio bridge
    bridge = AudioBridge(
        form_id=form_id,
        mode=mode,
        voice_config=voice_config,
        api_key=api_key
    )
    
    # Set up callbacks
    audio_playback = None
    audio_capture = None
    
    try:
        # Initialize audio I/O if pyaudio is available
        try:
            audio_playback = AudioPlayback(sample_rate=24000)
            audio_playback.start()
            
            audio_capture = AudioCapture(sample_rate=16000)
            audio_capture.start()
            
            print("✅ Audio I/O initialized")
        except ImportError:
            print("⚠️  pyaudio not available - audio I/O disabled")
            print("   Install with: pip install pyaudio")
            print("   Continuing with text-only mode...")
        except Exception as e:
            print(f"⚠️  Audio I/O error: {e}")
            print("   Continuing with text-only mode...")
        
        # Callback: Play agent audio output
        async def on_audio_output(audio_data: bytes):
            if audio_playback:
                try:
                    # Debug: Check if we got audio
                    if audio_data and len(audio_data) > 0:
                        print(f"🔊 Playing audio ({len(audio_data)} bytes)...", end="", flush=True)
                        await audio_playback.play_async(audio_data)
                        print(" ✅")
                    else:
                        print("⚠️  Received empty audio data")
                except Exception as e:
                    print(f"\n⚠️  Error playing audio: {e}")
            else:
                print("⚠️  Audio playback not available (pyaudio not installed or failed)")
        
        # Callback: Show transcriptions
        async def on_transcription(source: str, text: str):
            # Show both input and output transcriptions (word-by-word like original)
            if source == "input":
                print(f"👤 You: {text}")
            elif source == "output":
                # Show agent speech word-by-word (like the original working version)
                print(f"🤖 Agent: {text}")
        
        # Callback: Show agent text questions
        async def on_agent_text(text: str):
            print(f"\n🤖 Agent: {text}")
            print()  # Extra line for clarity
        
        bridge.on_audio_output = on_audio_output
        bridge.on_transcription = on_transcription
        bridge.on_agent_text = on_agent_text
        
        # Initialize bridge (connects to Live API, gets first question)
        print("\n🔄 Connecting to Gemini Live API...")
        await bridge.initialize()
        print("✅ Connected!\n")
        
        # Main conversation loop
        print("💬 Conversation started. Type your answers and press Enter.")
        print("   (Type 'quit' or 'exit' to end)")
        print()  # Extra line
        
        # Simplified: Just handle text input in a loop
        # The Live API audio is handled separately when questions are asked
        while not bridge.is_complete():
            try:
                # Get user input (blocking, but that's okay for CLI)
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(
                    None,
                    lambda: input("You: ").strip()
                )
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\n👋 Ending conversation...")
                    break
                
                # Process user input through agent
                await bridge.process_user_input(user_input)
                
                # Check if form is complete after processing
                if bridge.is_complete():
                    break
                    
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"⚠️  Error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(0.5)
        
        # Show results
        if bridge.is_complete():
            print("\n" + "=" * 60)
            print("✅ Form Complete!")
            print("=" * 60)
            print("\n📋 Collected Data:")
            
            collected = bridge.get_collected_data()
            for field_id, data in collected.items():
                value = data.get("value", "N/A")
                notes = data.get("notes", [])
                print(f"  {field_id}: {value}")
                if notes:
                    print(f"    Notes: {', '.join(notes)}")
            
            # Save to file
            from src.output_handlers import JSONOutputHandler, CSVOutputHandler
            
            json_handler = JSONOutputHandler()
            json_path = json_handler.save(collected, metadata={
                "mode": mode,
                "form_id": form_id,
                "voice_enabled": True,
                "voice_name": voice_config.voice_name,
            })
            print(f"\n💾 Saved to: {json_path}")
            
            csv_handler = CSVOutputHandler()
            csv_path = csv_handler.save(collected)
            print(f"💾 Appended to: {csv_path}")
    
    finally:
        # Cleanup
        print("\n🔄 Closing connections...")
        await bridge.close()
        
        if audio_capture:
            audio_capture.close()
        
        if audio_playback:
            audio_playback.close()
        
        print("✅ Done!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run voice-enabled intake form agent (V2 Audio)"
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
        default="Kore",
        help="Voice name (Kore, Charon, Fenrir, etc.)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit",
    )
    parser.add_argument(
        "--disable-audio",
        action="store_true",
        help="Disable audio I/O (text-only mode)",
    )
    
    args = parser.parse_args()
    
    if args.list_devices:
        print("🎤 Available Audio Devices:")
        print("=" * 60)
        devices = list_audio_devices()
        for dev in devices:
            print(f"  [{dev['index']}] {dev['name']}")
            print(f"      Input: {dev['channels_in']} channels, "
                  f"Output: {dev['channels_out']} channels")
        return
    
    # Create voice config
    voice_config = VoiceConfig(
        voice_name=args.voice,
        enable_affective_dialog=True,
        enable_thinking=True,
    )
    
    # Run async CLI
    try:
        asyncio.run(run_voice_cli(
            form_id=args.form_id,
            mode=args.mode,
            voice_config=voice_config
        ))
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

