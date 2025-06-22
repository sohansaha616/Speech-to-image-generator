import speech_recognition as sr
import pyaudio
import wave
import tempfile
import os
from openai import OpenAI
from utils import log_message

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.microphone_available = False
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Try to initialize microphone
        try:
            self.microphone = sr.Microphone()
            self.microphone_available = True
            
            # Adjust for ambient noise
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                log_message(f"Warning: Could not adjust for ambient noise: {str(e)}")
                
        except OSError as e:
            log_message(f"No audio input device available: {str(e)}")
            self.microphone_available = False
        except Exception as e:
            log_message(f"Error initializing microphone: {str(e)}")
            self.microphone_available = False
    
    def record_audio(self, duration=5, sample_rate=44100):
        """
        Record audio from microphone for specified duration
        
        Args:
            duration (int): Recording duration in seconds
            sample_rate (int): Sample rate for recording
            
        Returns:
            bytes: Audio data as bytes or None if failed
        """
        if not self.microphone_available:
            log_message("Microphone not available for recording")
            return None
            
        try:
            # Audio recording parameters
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Open stream
            stream = audio.open(
                format=format,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            log_message("Recording audio...")
            frames = []
            
            # Record for specified duration
            for _ in range(0, int(sample_rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            log_message("Audio recording completed")
            
            # Convert frames to bytes
            audio_data = b''.join(frames)
            
            # Create WAV file data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(audio.get_sample_size(format))
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)
                
                # Read the WAV file data
                with open(temp_file.name, 'rb') as f:
                    wav_data = f.read()
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                
                return wav_data
                
        except Exception as e:
            log_message(f"Error recording audio: {str(e)}")
            return None
    
    def speech_to_text(self, audio_file_path):
        """
        Convert speech in audio file to text using OpenAI Whisper
        
        Args:
            audio_file_path (str): Path to audio file
            
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            log_message("Starting speech-to-text conversion...")
            
            with open(audio_file_path, "rb") as audio_file:
                # Use OpenAI Whisper for transcription
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            transcribed_text = response.strip()
            log_message(f"Speech-to-text completed. Text length: {len(transcribed_text)} characters")
            
            return transcribed_text if transcribed_text else None
            
        except Exception as e:
            log_message(f"Error in speech-to-text conversion: {str(e)}")
            return None
    
    def speech_to_text_realtime(self, timeout=10):
        """
        Perform real-time speech-to-text conversion using microphone
        
        Args:
            timeout (int): Maximum time to wait for speech
            
        Returns:
            str: Transcribed text or None if failed
        """
        if not self.microphone_available:
            log_message("Microphone not available for real-time recognition")
            return None
            
        try:
            log_message("Starting real-time speech recognition...")
            
            if self.microphone is not None:
                with self.microphone as source:
                    # Listen for audio input
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                
                log_message("Audio captured, converting to text...")
                
                # Use OpenAI Whisper for transcription (more reliable than Google)
                return self._fallback_whisper_recognition(audio)
            else:
                log_message("Microphone not initialized")
                return None
                
        except sr.WaitTimeoutError:
            log_message("No speech detected within timeout period")
            return None
        except Exception as e:
            log_message(f"Error in real-time speech recognition: {str(e)}")
            return None
    
    def _fallback_whisper_recognition(self, audio_data):
        """
        Fallback method using OpenAI Whisper for speech recognition
        
        Args:
            audio_data: AudioData object from speech_recognition
            
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            # Convert AudioData to WAV format
            wav_data = audio_data.get_wav_data()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_data)
                temp_file_path = temp_file.name
            
            # Use Whisper for transcription
            result = self.speech_to_text(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return result
            
        except Exception as e:
            log_message(f"Error in Whisper fallback recognition: {str(e)}")
            return None
    
    def test_microphone(self):
        """
        Test if microphone is working properly
        
        Returns:
            bool: True if microphone is working, False otherwise
        """
        if not self.microphone_available:
            return False
            
        try:
            if self.microphone is not None:
                with self.microphone as source:
                    # Try to capture a short audio sample
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
                    return True
            else:
                return False
        except Exception as e:
            log_message(f"Microphone test failed: {str(e)}")
            return False
