import hashlib
import os
import queue
import threading
from datetime import datetime

import scipy
import torch
from transformers import AutoTokenizer, VitsModel

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import TaskStatus

# Setup logger for this module
logger = get_logger(__name__)


class TTSEngine:
    def __init__(self, device=None):
        logger.info("TTS engine: Loading Last Whisper TTS model...")

        # Device detection and setup
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"TTS engine: Using device: {self.device}")

        # Load model and tokenizer
        self.model = VitsModel.from_pretrained("facebook/mms-tts-fin")
        self.tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-fin")

        # Move model to the specified device
        self.model = self.model.to(self.device)

        self.request_queue = queue.Queue()
        # New task queue for external services to consume
        self.task_message_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None

        # Create output directory if it doesn't exist
        self.output_dir = settings.audio_dir
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"TTS engine: TTS model loaded successfully on {self.device}!")

    def get_task_message_queue(self):
        """Returns the task queue for external services to consume task messages"""
        return self.task_message_queue

    def start_service(self):
        """Start the TTS service worker thread"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
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
        if not text.strip():
            logger.error("Error: Empty text provided")
            return None

        # Validate language support
        if language not in settings.tts_supported_languages:
            logger.error(
                f"Error: Language '{language}' is not supported. Supported languages: {settings.tts_supported_languages}")
            return None

        # Generate filename based on timestamp and text hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]

        if custom_filename:
            # Remove extension if provided and add .wav
            base_filename = os.path.splitext(custom_filename)[0] + ".wav"
        else:
            base_filename = f"tts_{timestamp}_{text_hash}.wav"

        # Save to output directory
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

        # Publish initial task message to external queue
        self._publish_task_message(request_id, filename, "queued", text=text, language=language)

        logger.info(f"TTS engine: Request {request_id} submitted and queued. Output file: {filename}")
        return request_id

    def _publish_task_message(self, request_id, output_file_path, status, **metadata):
        """Publish a task message to the external task queue"""
        task_message = {
            "request_id": request_id,
            "output_file_path": output_file_path,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
        }
        self.task_message_queue.put_nowait(task_message)

    def _process_queue(self):
        """Worker thread function to process queued requests"""
        while self.is_running:
            try:
                # Get request from queue with timeout
                request = self.request_queue.get(timeout=1)
                self._process_request(request)
                self.request_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")

    def _process_request(self, request):
        """Process a single TTS request"""
        try:
            logger.info(f"TTS engine: Processing request {request['id']} on {self.device}...")
            request["status"] = TaskStatus.PROCESSING

            # Publish processing status
            self._publish_task_message(
                request["id"],
                request["filename"],
                TaskStatus.PROCESSING,
                text=request["text"],
                language=request["language"],
                started_at=datetime.now().isoformat(),
                device=str(self.device),
            )

            # Tokenize the text and move to device
            inputs = self.tokenizer(request["text"], return_tensors="pt")
            # Move input tensors to the same device as the model
            inputs = {key: value.to(self.device) for key, value in inputs.items()}

            # Generate audio
            with torch.no_grad():
                output = self.model(**inputs).waveform
                audio_data = output.squeeze().cpu().numpy()

            # Save audio file
            scipy.io.wavfile.write(
                request["filename"], rate=self.model.config.sampling_rate, data=audio_data
            )

            request["status"] = TaskStatus.COMPLETED
            request["completed_at"] = datetime.now()

            # Publish completion status
            self._publish_task_message(
                request["id"],
                request["filename"],
                TaskStatus.COMPLETED,
                text=request["text"],
                language=request["language"],
                completed_at=request["completed_at"].isoformat(),
                file_size=(
                    os.path.getsize(request["filename"])
                    if os.path.exists(request["filename"])
                    else None
                ),
                sampling_rate=self.model.config.sampling_rate,
                device=str(self.device),
            )

            # Send 'done' message to indicate task is fully finished
            self._publish_task_message(
                request["id"],
                request["filename"],
                TaskStatus.DONE,
                text=request["text"],
                language=request["language"],
                completed_at=request["completed_at"].isoformat(),
                file_size=(
                    os.path.getsize(request["filename"])
                    if os.path.exists(request["filename"])
                    else None
                ),
                sampling_rate=self.model.config.sampling_rate,
                device=str(self.device),
            )

            logger.info(
                f"TTS engine: Request {request['id']} completed successfully! Audio saved as: {request['filename']}")

        except Exception as e:
            request["status"] = TaskStatus.FAILED
            request["error"] = str(e)

            # Publish failure status
            self._publish_task_message(
                request["id"],
                request["filename"],
                TaskStatus.FAILED,
                text=request["text"],
                language=request["language"],
                error=str(e),
                failed_at=datetime.now().isoformat(),
                device=str(self.device),
            )
            logger.error(f"Request {request['id']} failed: {e}")

    def get_queue_size(self):
        """Get the current queue size"""
        return self.request_queue.qsize()

    def get_task_message_queue_size(self):
        """Get the current task queue size"""
        return self.task_message_queue.qsize()

    def get_device_info(self):
        """Get information about the current device being used"""
        device_info = {
            "device": str(self.device),
            "device_type": self.device.type,
            "cuda_available": torch.cuda.is_available(),
        }

        if torch.cuda.is_available() and self.device.type == "cuda":
            device_info.update(
                {
                    "cuda_device_count": torch.cuda.device_count(),
                    "cuda_device_name": torch.cuda.get_device_name(self.device),
                    "cuda_memory_allocated": torch.cuda.memory_allocated(self.device),
                    "cuda_memory_reserved": torch.cuda.memory_reserved(self.device),
                }
            )

        return device_info

    def switch_device(self, new_device):
        """Switch the model to a different device (CPU/GPU)"""
        try:
            old_device = self.device
            self.device = torch.device(new_device)
            self.model = self.model.to(self.device)
            logger.info(f"TTS engine: Successfully switched from {old_device} to {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to {new_device}: {e}")
            return False
