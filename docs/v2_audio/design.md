# V2 Audio: Voice-Enabled Intake Form Agent

## Overview

V2 Audio extends the V2.0 intake form agent with **Gemini Live API** integration, enabling natural voice conversations for form filling. Users can speak their answers instead of typing, and the agent responds with synthesized speech.

## Architecture

### Two-Way Audio Flow

```
User speaks (audio) 
  ↓
Gemini Live API transcribes → text
  ↓
Our LangGraph agent processes (validation, extraction, etc.)
  ↓
Agent generates text question/response
  ↓
Gemini Live API converts to audio
  ↓
User hears question (audio)
  ↓
[Loop continues]
```

### Key Components

1. **Voice Session Manager** (`src/v2_audio/voice_session.py`)
   - Manages Gemini Live API connection
   - Handles audio input/output streaming
   - Bridges between Live API and our LangGraph agent

2. **Audio Bridge** (`src/v2_audio/audio_bridge.py`)
   - Converts agent text → Live API audio output
   - Receives Live API transcriptions → agent text input
   - Manages session state synchronization

3. **Voice CLI** (`src/main_v2_audio.py`)
   - Interactive voice-based form filling
   - Handles microphone input, speaker output
   - Manages conversation flow

4. **Voice API** (`src/v2_audio/api.py`)
   - WebSocket endpoint for browser-based voice UI
   - Real-time audio streaming
   - Session management

## Implementation Approach

### Option 1: Hybrid Bridge (Recommended)

**How it works:**
- Our LangGraph agent handles all form logic (validation, extraction, field progression)
- Gemini Live API acts as voice interface layer:
  - Receives user audio → transcribes to text → sends to agent
  - Receives agent text → converts to audio → plays to user

**Pros:**
- Keeps all existing validation/processing logic
- Clean separation of concerns
- Easy to test (can still use text mode)
- Can switch between voice/text seamlessly

**Cons:**
- Two API calls per turn (Live API + our agent)
- Slightly higher latency

### Option 2: Full Live API Integration

**How it works:**
- Replace text agent entirely with Live API
- Use Live API's native conversation capabilities
- Add structured prompts to guide form filling

**Pros:**
- Lower latency (single API)
- More natural conversation flow
- Native audio features (affective dialog, thinking)

**Cons:**
- Lose structured validation logic
- Harder to enforce form schema
- More complex prompt engineering

**Recommendation: Use Option 1 (Hybrid Bridge)**

## Features to Implement

### Phase 1: Basic Voice Interface
- [ ] Connect to Gemini Live API
- [ ] Text-to-speech for agent questions
- [ ] Speech-to-text for user answers
- [ ] Basic conversation loop

### Phase 2: Enhanced Audio Features
- [ ] Voice Activity Detection (VAD) - detect when user is speaking
- [ ] Interrupt handling - user can interrupt agent mid-sentence
- [ ] Multiple voice options (Kore, Charon, etc.)
- [ ] Audio transcription display (show text while speaking)

### Phase 3: Advanced Features
- [ ] Affective dialog (emotion-aware responses)
- [ ] Proactive audio (agent decides when to respond)
- [ ] Thinking mode (show agent "thinking" indicators)
- [ ] Multi-language support
- [ ] Session resumption (pause/resume conversations)

### Phase 4: Web Integration
- [ ] WebSocket API for browser-based voice UI
- [ ] Real-time audio streaming
- [ ] Visual feedback (waveforms, transcription)
- [ ] Mobile-friendly voice interface

## Technical Details

### Gemini Live API Configuration

```python
from google import genai
from google.genai import types

client = genai.Client()

model = "gemini-2.5-flash-native-audio-preview-09-2025"

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config={
        "voice_config": {
            "prebuilt_voice_config": {"voice_name": "Kore"}
        }
    },
    input_audio_transcription={},  # Transcribe user input
    output_audio_transcription={},  # Transcribe agent output
    enable_affective_dialog=True,   # Emotion-aware
    proactivity={"proactive_audio": True},
    thinking_config=types.ThinkingConfig(
        thinking_budget=1024,
        include_thoughts=True
    )
)
```

### Audio Format Requirements

- **Input**: Raw PCM, 16-bit, little-endian, 16kHz sample rate
- **Output**: 24kHz sample rate (Live API handles conversion)
- **MIME type**: `audio/pcm;rate=16000`

### Session Flow

1. **Initialize:**
   - Create LangGraph session (as in V2.0)
   - Connect to Gemini Live API
   - Set up audio I/O streams

2. **Conversation Loop:**
   ```
   while not form_complete:
       # Agent generates text question
       agent_text = get_next_question_from_graph()
       
       # Send to Live API for audio output
       await live_session.send_client_content(
           turns={"role": "user", "parts": [{"text": agent_text}]},
           turn_complete=True
       )
       
       # Receive audio response
       async for response in live_session.receive():
           if response.server_content.output_audio:
               # Play audio to user
               play_audio(response.server_content.output_audio)
           
           if response.server_content.input_transcription:
               # User spoke - get transcription
               user_text = response.server_content.input_transcription.text
               
               # Send to our agent for processing
               process_with_agent(user_text)
   ```

3. **Cleanup:**
   - Close Live API session
   - Save form data
   - Clean up audio streams

## File Structure

```
src/v2_audio/
├── __init__.py
├── voice_session.py      # Live API connection management
├── audio_bridge.py       # Bridge between agent and Live API
├── audio_utils.py        # Audio format conversion, I/O
├── api.py                # WebSocket API for web clients
└── config.py             # Voice-specific configuration

src/
└── main_v2_audio.py      # CLI entry point for voice mode

examples/
└── voice_client_example.py  # Example voice client

tests/
└── test_v2_audio_*.py    # Tests for voice features
```

## Dependencies

```txt
google-genai>=0.2.0        # Gemini Live API client
pyaudio>=0.2.11            # Audio I/O (microphone, speaker)
numpy>=1.24.0              # Audio processing
websockets>=12.0            # WebSocket support for web API
```

## Usage Examples

### CLI Voice Mode

```bash
# Start voice-enabled form filling
python -m src.main_v2_audio --form-id employment_onboarding --mode quality

# With specific voice
python -m src.main_v2_audio --form-id rental_application --voice Kore
```

### WebSocket API

```javascript
// Browser client example
const ws = new WebSocket('ws://localhost:8000/api/voice/start');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'audio') {
        playAudio(data.audio);  // Play agent's voice
    } else if (data.type === 'transcription') {
        showText(data.text);    // Show transcription
    }
};

// Send user audio
navigator.mediaDevices.getUserMedia({audio: true})
    .then(stream => {
        // Capture audio and send via WebSocket
    });
```

## Next Steps

1. **Research & Setup:**
   - Install `google-genai` package
   - Test Live API connection
   - Verify audio I/O libraries work on target platforms

2. **Implement Core Bridge:**
   - Create `voice_session.py` with Live API connection
   - Implement text → audio conversion
   - Implement audio → text transcription

3. **Integrate with Agent:**
   - Connect Live API to existing LangGraph agent
   - Test end-to-end voice conversation

4. **Add Features:**
   - VAD and interrupt handling
   - Voice selection
   - Transcription display

5. **Web Integration:**
   - WebSocket API
   - Browser client example

