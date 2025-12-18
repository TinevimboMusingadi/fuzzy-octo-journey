# V2 Audio Implementation Guide

## Overview

V2 Audio integrates **Gemini Live API** with the existing V2.0 intake form agent to enable voice-based form filling. Users can speak their answers, and the agent responds with synthesized speech.

## Architecture

### Hybrid Bridge Approach

```
┌─────────────────┐
│   User Audio    │
│  (Microphone)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini Live    │
│     API         │
│  (Transcribe)   │
└────────┬────────┘
         │ Text
         ▼
┌─────────────────┐
│  LangGraph      │
│    Agent        │
│ (Process/Validate)│
└────────┬────────┘
         │ Text Question
         ▼
┌─────────────────┐
│  Gemini Live    │
│     API         │
│  (Text-to-Speech)│
└────────┬────────┘
         │ Audio
         ▼
┌─────────────────┐
│  User Hears     │
│  (Speaker)      │
└─────────────────┘
```

### Key Components

1. **VoiceSession** (`src/v2_audio/voice_session.py`)
   - Manages Gemini Live API connection
   - Handles audio streaming and transcription
   - Configures voice, VAD, and advanced features

2. **AudioBridge** (`src/v2_audio/audio_bridge.py`)
   - Bridges LangGraph agent with Live API
   - Converts agent text → Live API audio
   - Converts Live API transcriptions → agent input

3. **AudioUtils** (`src/v2_audio/audio_utils.py`)
   - Microphone capture (AudioCapture)
   - Speaker playback (AudioPlayback)
   - Audio format conversion

4. **Main CLI** (`src/main_v2_audio.py`)
   - Interactive voice-based form filling
   - Handles both voice and text input
   - Manages conversation flow

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key new dependencies:
- `google-genai>=0.2.0` - Gemini Live API client
- `pyaudio>=0.2.11` - Audio I/O (optional, for local audio)
- `numpy>=1.24.0` - Audio processing

### 2. Configure Environment

Add to `.env`:
```
GOOGLE_API_KEY=your_api_key_here
LIVE_API_MODEL=gemini-2.5-flash-native-audio-preview-09-2025
VOICE_NAME=Kore
ENABLE_AFFECTIVE_DIALOG=true
ENABLE_THINKING=true
```

### 3. Test Audio Devices (Optional)

```bash
python -m src.main_v2_audio --list-devices
```

## Usage

### Basic Voice Mode

```bash
python -m src.main_v2_audio --form-id employment_onboarding --mode quality
```

### With Custom Voice

```bash
python -m src.main_v2_audio --form-id rental_application --voice Charon
```

### Text-Only Mode (No Audio I/O)

```bash
python -m src.main_v2_audio --form-id tax_1040_mvp --disable-audio
```

## How It Works

### 1. Initialization

1. Create LangGraph session (same as V2.0)
2. Connect to Gemini Live API
3. Initialize audio I/O (microphone/speaker)
4. Run agent to get first question
5. Send question text to Live API → converts to audio

### 2. Conversation Loop

```
while not form_complete:
    # User speaks → Live API transcribes → Agent processes
    # Agent generates question → Live API speaks → User hears
```

### 3. Audio Flow

**User Input:**
- Microphone captures audio (16kHz PCM)
- Send to Live API via `send_realtime_input()`
- Live API transcribes → text
- Text sent to LangGraph agent

**Agent Output:**
- Agent generates text question
- Send to Live API via `send_client_content()`
- Live API converts to audio (24kHz)
- Play audio through speaker

## Advanced Features

### Voice Activity Detection (VAD)

Automatically detects when user is speaking:
- Starts listening when user begins speaking
- Stops when user pauses
- Configurable sensitivity levels

### Interruption Handling

User can interrupt agent mid-sentence:
- Agent stops speaking immediately
- User's input is processed
- Agent responds to new input

### Affective Dialog

Emotion-aware responses:
- Agent adapts tone based on user's expression
- More natural, empathetic conversations
- Enabled by default

### Thinking Mode

Shows agent "thinking" process:
- Visual/audio indicators during processing
- Helps users understand agent is working
- Configurable thinking budget

## Troubleshooting

### Audio I/O Issues

**Problem:** "pyaudio not available"
- **Solution:** Install pyaudio: `pip install pyaudio`
- **Note:** On some systems, you may need system audio libraries:
  - Linux: `sudo apt-get install portaudio19-dev`
  - macOS: Usually works out of the box
  - Windows: Usually works out of the box

**Problem:** "No audio devices found"
- **Solution:** Check audio devices: `--list-devices`
- **Solution:** Ensure microphone/speaker are connected and enabled

### Live API Issues

**Problem:** "API key not found"
- **Solution:** Set `GOOGLE_API_KEY` in `.env` or environment

**Problem:** "Model not available"
- **Solution:** Check model name in config
- **Solution:** Ensure API key has access to Live API

**Problem:** "Connection timeout"
- **Solution:** Check internet connection
- **Solution:** Verify API key is valid

### Performance Issues

**Problem:** High latency
- **Solution:** Use `speed` mode instead of `quality`
- **Solution:** Reduce thinking budget
- **Solution:** Disable affective dialog if not needed

## Next Steps

### Phase 1: WebSocket API
- Add WebSocket endpoint for browser-based voice UI
- Real-time audio streaming
- Session management

### Phase 2: Mobile Support
- iOS/Android voice clients
- Push-to-talk interface
- Background audio processing

### Phase 3: Multi-language
- Automatic language detection
- Language-specific voice models
- Translation support

## File Structure

```
src/v2_audio/
├── __init__.py
├── config.py              # Voice configuration
├── voice_session.py       # Live API session management
├── audio_bridge.py        # Agent ↔ Live API bridge
└── audio_utils.py         # Audio I/O utilities

src/
└── main_v2_audio.py       # CLI entry point

docs/v2_audio/
├── design.md              # Design document
└── IMPLEMENTATION.md      # This file
```

## API Reference

### VoiceConfig

```python
@dataclass
class VoiceConfig:
    model: str = "gemini-2.5-flash-native-audio-preview-09-2025"
    response_modality: Literal["AUDIO", "TEXT"] = "AUDIO"
    voice_name: str = "Kore"
    enable_input_transcription: bool = True
    enable_output_transcription: bool = True
    enable_affective_dialog: bool = True
    enable_proactive_audio: bool = False
    enable_thinking: bool = True
    thinking_budget: int = 1024
    vad_enabled: bool = True
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
```

### AudioBridge

```python
bridge = AudioBridge(
    form_id="employment_onboarding",
    mode="quality",
    voice_config=VoiceConfig(),
    api_key=os.getenv("GOOGLE_API_KEY")
)

await bridge.initialize()
await bridge.process_user_input("U.S. citizen")
await bridge.listen_and_process()
```

## Examples

See `examples/voice_client_example.py` for a complete example.

