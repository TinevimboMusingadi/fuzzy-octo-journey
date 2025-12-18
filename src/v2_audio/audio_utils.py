"""Audio I/O utilities for microphone and speaker handling."""

import asyncio
import queue
from typing import Optional, Callable, Awaitable
import numpy as np

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


class AudioCapture:
    """Captures audio from microphone in real-time."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        device_index: Optional[int] = None
    ):
        """Initialize audio capture."""
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "pyaudio is required for audio capture. "
                "Install with: pip install pyaudio"
            )
        
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
    
    def start(self):
        """Start audio capture stream."""
        if self.stream:
            return
        
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.is_recording = True
        self.stream.start_stream()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def read_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """Read a chunk of audio data."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    async def read_async(self) -> Optional[bytes]:
        """Read audio chunk asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_chunk)
    
    def stop(self):
        """Stop audio capture."""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def close(self):
        """Close audio resources."""
        self.stop()
        if self.audio:
            self.audio.terminate()
            self.audio = None


class AudioPlayback:
    """Plays audio to speaker in real-time."""
    
    def __init__(
        self,
        sample_rate: int = 24000,
        chunk_size: int = 1024,
        channels: int = 1,
        device_index: Optional[int] = None
    ):
        """Initialize audio playback."""
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "pyaudio is required for audio playback. "
                "Install with: pip install pyaudio"
            )
        
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
    
    def start(self):
        """Start audio playback stream."""
        if self.stream:
            return
        
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.device_index,
            frames_per_buffer=self.chunk_size
        )
    
    def play(self, audio_data: bytes):
        """Play audio data."""
        if self.stream:
            self.stream.write(audio_data)
    
    async def play_async(self, audio_data: bytes):
        """Play audio data asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.play, audio_data)
    
    def stop(self):
        """Stop audio playback."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def close(self):
        """Close audio resources."""
        self.stop()
        if self.audio:
            self.audio.terminate()
            self.audio = None


def convert_sample_rate(
    audio_data: bytes,
    input_rate: int,
    output_rate: int,
    channels: int = 1
) -> bytes:
    """Convert audio sample rate (simple linear interpolation)."""
    if input_rate == output_rate:
        return audio_data
    
    # Convert bytes to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # Reshape if stereo
    if channels > 1:
        audio_array = audio_array.reshape(-1, channels)
    
    # Calculate resampling ratio
    ratio = output_rate / input_rate
    new_length = int(len(audio_array) * ratio)
    
    # Simple linear interpolation (for production, use scipy.signal.resample)
    indices = np.linspace(0, len(audio_array) - 1, new_length)
    resampled = np.interp(indices, np.arange(len(audio_array)), audio_array)
    
    # Convert back to int16
    resampled = resampled.astype(np.int16)
    
    # Convert back to bytes
    return resampled.tobytes()


def list_audio_devices() -> list:
    """List available audio input/output devices."""
    if not PYAUDIO_AVAILABLE:
        return []
    
    audio = pyaudio.PyAudio()
    devices = []
    
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        devices.append({
            "index": i,
            "name": info["name"],
            "channels_in": info["maxInputChannels"],
            "channels_out": info["maxOutputChannels"],
            "sample_rate": int(info["defaultSampleRate"]),
        })
    
    audio.terminate()
    return devices

