import hashlib
import os
import queue
import random
import threading
import wave
from datetime import datetime

from azure.cognitiveservices import speech

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import TaskStatus

# Setup logger for this module
logger = get_logger(__name__)


class TTSEngine:
    """
    Drop-in replacement using Microsoft Azure Speech (Neural, fi-FI).
    - Same public methods and message flow as your existing engine.
    - Randomly selects one of the configured Finnish neural voices per request.
    - Writes WAV (RIFF) 24kHz 16-bit mono files by default.
    """

    def __init__(
        self,
        voices=None,  # list of azure voice names to choose from
        language_code: str = "fi-FI",
        sample_rate_hz: int = 24000,  # RIFF 24k mono PCM
        speaking_rate: float = 1.0,  # use SSML <prosody rate="...">
        pitch: float = 0.0,  # use SSML <prosody pitch="...">
        volume_gain_db: float = 0.0,  # use SSML <prosody volume="...dB">
        use_ssml: bool = False,  # set True to enable prosody controls
        # for short sentences you don't need chunking; left here for parity
        max_chars_per_request: int = 4500,  # Azure limit is 5000 chars
        device=None,  # for API compatibility (not used for Azure)
    ):
        logger.info("TTS engine: Initializing Azure Speech client...")

        # Credentials: prefer your settings module, fall back to env vars
        self.azure_key = getattr(settings, "azure_speech_key", None) or os.getenv(
            "AZURE_SPEECH_KEY"
        )
        self.azure_region = getattr(settings, "azure_speech_region", None) or os.getenv(
            "AZURE_SPEECH_REGION"
        )

        if not self.azure_key or not self.azure_region:
            raise RuntimeError(
                "Azure Speech credentials missing. Set settings.azure_speech_{key,region} "
                "or AZURE_SPEECH_KEY / AZURE_SPEECH_REGION env vars."
            )

        self.language_code = language_code
        self.sample_rate_hz = sample_rate_hz
        self.speaking_rate = speaking_rate
        self.pitch = pitch
        self.volume_gain_db = volume_gain_db
        self.use_ssml = use_ssml
        self.max_chars_per_request = max_chars_per_request

        # Device field for API compatibility (not used for Azure API)
        self.device = device or "azure-speech-api"

        # Supported Finnish neural voices — random selection per request
        self.voices = voices or [
            "fi-FI-HarriNeural",
            "fi-FI-NooraNeural",
            "fi-FI-SelmaNeural",
        ]

        # Queues & worker lifecycle
        self.request_queue = queue.Queue()
        self.task_message_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None

        # Output directory
        self.output_dir = settings.audio_dir
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(
            f"TTS engine: Azure Speech ready "
            f"(voices={self.voices}, lang={self.language_code}, sr={self.sample_rate_hz} Hz)"
        )

    # ----------------------- Public API (unchanged) -----------------------

    def get_task_message_queue(self):
        """Returns the task queue for external services to consume task messages"""
        return self.task_message_queue

    def start_service(self):
        """Start the TTS service worker thread"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(
                target=self._process_queue, daemon=True
            )
            self.worker_thread.start()
            logger.info("TTS engine: Service started successfully!")

    def stop_service(self):
        """Stop the TTS service"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
            self.worker_thread = None
        logger.info("TTS engine: Service stopped successfully!")

    def submit_request(self, text, custom_filename=None, language="fi"):
        """Submit a text-to-speech conversion request"""
        if not text or not str(text).strip():
            logger.error("Error: Empty text provided")
            return None

        if language not in settings.tts_supported_languages:
            logger.error(
                f"Error: Language '{language}' is not supported. "
                f"Supported languages: {settings.tts_supported_languages}"
            )
            return None

        # Generate filename based on timestamp + hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]

        if custom_filename:
            base_filename = os.path.splitext(custom_filename)[0] + ".wav"
        else:
            base_filename = f"tts_{timestamp}_{text_hash}.wav"

        filename = os.path.join(self.output_dir, base_filename)

        request_id = f"{timestamp}_{text_hash}"
        request = {
            "id": request_id,
            "text": text,
            "filename": filename,
            "language": language,
            "status": "queued",
            "submitted_at": datetime.now(),
        }

        self.request_queue.put_nowait(request)

        # Publish initial task message
        self._publish_task_message(
            request_id,
            filename,
            "queued",
            text=text,
            language=language,
        )

        logger.info(
            f"TTS engine: Request {request_id} submitted and queued. "
            f"Output file: {filename}"
        )
        return request_id

    def get_queue_size(self):
        """Get the current queue size"""
        return self.request_queue.qsize()

    def get_task_message_queue_size(self):
        """Get the current task queue size"""
        return self.task_message_queue.qsize()

    def get_device_info(self):
        """API 'device' info (mirrors your original signature)"""
        return {
            "device": self.device,
            "device_type": "api",
            "cuda_available": False,
        }

    def switch_device(self, new_device):
        """Not applicable; present for interface compatibility."""
        logger.info(
            f"TTS engine: switch_device requested ({new_device}) — "
            f"ignored for API backend."
        )
        return False

    # ----------------------- Internal helpers -----------------------

    def _publish_task_message(self, request_id, output_file_path, status, **metadata):
        task_message = {
            "request_id": request_id,
            "output_file_path": output_file_path,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
        }
        self.task_message_queue.put_nowait(task_message)

    def _process_queue(self):
        while self.is_running:
            try:
                request = self.request_queue.get(timeout=1)
                self._process_request(request)
                self.request_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")

    def _process_request(self, request):
        try:
            selected_voice = random.choice(self.voices)
            logger.info(
                f"TTS engine: Processing request {request['id']} with Azure TTS "
                f"(voice={selected_voice})..."
            )
            request["status"] = TaskStatus.PROCESSING

            self._publish_task_message(
                request["id"],
                request["filename"],
                TaskStatus.PROCESSING,
                text=request["text"],
                language=request["language"],
                started_at=datetime.now().isoformat(),
                backend="azure-tts",
                voice=selected_voice,
                device=self.device,
                sample_rate_hz=self.sample_rate_hz,
                speaking_rate=self.speaking_rate,
                pitch=self.pitch,
                volume_gain_db=self.volume_gain_db,
            )

            # Synthesize to WAV file
            total_frames = self._synthesize_to_wav(
                text=request["text"],
                wav_path=request["filename"],
                voice_name=selected_voice,
            )

            request["status"] = TaskStatus.COMPLETED
            request["completed_at"] = datetime.now()

            # Publish completion + done
            meta = {
                "text": request["text"],
                "language": request["language"],
                "completed_at": request["completed_at"].isoformat(),
                "file_size": (
                    os.path.getsize(request["filename"])
                    if os.path.exists(request["filename"])
                    else None
                ),
                "sampling_rate": self.sample_rate_hz,
                "frames": total_frames,
                "backend": "azure-tts",
                "voice": selected_voice,
                "device": self.device,
            }
            self._publish_task_message(
                request["id"], request["filename"], TaskStatus.COMPLETED, **meta
            )
            self._publish_task_message(
                request["id"], request["filename"], TaskStatus.DONE, **meta
            )

            logger.info(
                f"TTS engine: Request {request['id']} completed! "
                f"Saved: {request['filename']}"
            )

        except Exception as e:
            request["status"] = TaskStatus.FAILED
            request["error"] = str(e)
            self._publish_task_message(
                request["id"],
                request["filename"],
                TaskStatus.FAILED,
                text=request["text"],
                language=request["language"],
                error=str(e),
                failed_at=datetime.now().isoformat(),
                backend="azure-tts",
                device=self.device,
            )
            logger.error(f"Request {request['id']} failed: {e}")

    def _synthesize_to_wav(self, text: str, wav_path: str, voice_name: str) -> int:
        """
        Synthesize `text` (or SSML) to a single WAV file at self.sample_rate_hz.
        Returns total frames written (16-bit mono).
        """
        speech_config = speech.SpeechConfig(
            subscription=self.azure_key, region=self.azure_region
        )

        # Voice & output format
        speech_config.speech_synthesis_voice_name = voice_name
        # RIFF (WAV) 24kHz 16-bit mono PCM
        speech_config.set_speech_synthesis_output_format(
            speech.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
        )

        # Output target (file)
        os.makedirs(os.path.dirname(wav_path), exist_ok=True)
        audio_config = speech.audio.AudioOutputConfig(filename=wav_path)

        synthesizer = speech.SpeechSynthesizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Build SSML if requested (enables rate/pitch/volume tweaks)
        if self.use_ssml:
            # Convert numeric controls to SSML-friendly strings
            # speaking_rate: 1.0 -> "0%", 1.1->"10%", 0.9->"-10%"
            rate_pct = f"{int(round((self.speaking_rate - 1.0) * 100))}%"
            pitch_st = f"{self.pitch:+.2f}st"  # semitones, e.g. +2.00st
            vol_db = f"{self.volume_gain_db:+.1f}dB"  # e.g. +3.0dB

            ssml = f"""
            <speak version="1.0" xml:lang="{self.language_code}">
              <voice name="{voice_name}">
                <prosody rate="{rate_pct}" pitch="{pitch_st}" volume="{vol_db}">
                  {speech.ssml.escape_xml(text)}
                </prosody>
              </voice>
            </speak>
            """.strip()

            result = synthesizer.speak_ssml_async(ssml).get()
        else:
            result = synthesizer.speak_text_async(text).get()

        # Handle result
        if result.reason == speech.ResultReason.SynthesizingAudioCompleted:
            # Determine total frames from output WAV (re-open to count)
            with wave.open(wav_path, "rb") as wf:
                frames = wf.getnframes()
            return frames

        if result.reason == speech.ResultReason.Canceled:
            details = speech.CancellationDetails(result)
            raise RuntimeError(
                f"Azure synthesis canceled: reason={details.reason}, "
                f"error={getattr(details, 'error_details', None)}"
            )

        raise RuntimeError(f"Azure synthesis failed: reason={result.reason}")
