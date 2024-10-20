import pyaudio
import wave
import threading
import queue
from pydub import AudioSegment
from pydub.playback import play
import webrtcvad
import collections
import struct

class AudioHandler:
    def __init__(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK_DURATION_MS = 30  # Duration of each audio chunk (ms)
        self.PADDING_DURATION_MS = 300  # Silent time added before and after speech (ms)
        self.CHUNK_SIZE = int(self.RATE * self.CHUNK_DURATION_MS / 1000)
        self.PADDING_CHUNKS = int(self.PADDING_DURATION_MS / self.CHUNK_DURATION_MS)
        self.NUM_PADDING_CHUNKS = int(self.PADDING_DURATION_MS / self.CHUNK_DURATION_MS)
        self.NUM_WINDOW_CHUNKS = int(240 / self.CHUNK_DURATION_MS)
        self.ring_buffer = collections.deque(maxlen=self.NUM_PADDING_CHUNKS)
        self.triggered = False
        self.voiced_frames = []
        self.recording = False
        self.vad = webrtcvad.Vad(3)  # Set VAD sensitivity (0-3)
        self.audio_queue = queue.Queue()

    def start_listening(self):
        self.recording = True
        threading.Thread(target=self._listen_and_record).start()

    def stop_listening(self):
        self.recording = False

    def _listen_and_record(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK_SIZE)

        while self.recording:
            chunk = stream.read(self.CHUNK_SIZE)
            is_speech = self.vad.is_speech(chunk, self.RATE)

            if not self.triggered:
                self.ring_buffer.append((chunk, is_speech))
                num_voiced = len([f for f, speech in self.ring_buffer if speech])
                if num_voiced > 0.9 * self.ring_buffer.maxlen:
                    self.triggered = True
                    for f, s in self.ring_buffer:
                        self.voiced_frames.append(f)
                    self.ring_buffer.clear()
            else:
                self.voiced_frames.append(chunk)
                self.ring_buffer.append((chunk, is_speech))
                num_unvoiced = len([f for f, speech in self.ring_buffer if not speech])
                if num_unvoiced > 0.9 * self.ring_buffer.maxlen:
                    self.triggered = False
                    audio_data = b''.join(self.voiced_frames)
                    self.audio_queue.put(audio_data)
                    self.voiced_frames = []
                    self.ring_buffer.clear()

        stream.stop_stream()
        stream.close()
        p.terminate()

    def get_audio_data(self):
        if not self.audio_queue.empty():
            return self.audio_queue.get()
        return None

    def play_audio(self, audio_data):
        audio = AudioSegment.from_mp3(audio_data)
        play(audio)

audio_handler = AudioHandler()
