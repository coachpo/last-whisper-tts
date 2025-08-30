"""TTS service wrapper."""

from typing import Optional

from app.core.config import settings
from app.core.exceptions import TTSServiceException


class TTSEngineWrapper:
    """Wrapper for the TTS service that provides a clean interface."""

    def __init__(self):
        self._service: Optional[object] = None
        self._is_initialized = False

    def initialize(self):
        """Initialize the TTS service."""
        try:
            # Get TTS provider from settings, default to 'local'
            provider = getattr(settings, 'tts_provider', 'local').lower()

            if provider == 'local':
                from app.tts_engine.tts_engine_local import TTSEngine
                self._service = TTSEngine(device=settings.tts_device)
            elif provider == 'azure':
                from app.tts_engine.tts_engine_azure import TTSEngine
                # Azure-specific configuration
                azure_config = {}
                if hasattr(settings, 'azure_voices'):
                    azure_config['voices'] = settings.azure_voices
                if hasattr(settings, 'azure_language_code'):
                    azure_config['language_code'] = settings.azure_language_code
                if hasattr(settings, 'azure_sample_rate_hz'):
                    azure_config['sample_rate_hz'] = settings.azure_sample_rate_hz
                if hasattr(settings, 'azure_speaking_rate'):
                    azure_config['speaking_rate'] = settings.azure_speaking_rate
                if hasattr(settings, 'azure_pitch'):
                    azure_config['pitch'] = settings.azure_pitch
                if hasattr(settings, 'azure_volume_gain_db'):
                    azure_config['volume_gain_db'] = settings.azure_volume_gain_db
                if hasattr(settings, 'azure_use_ssml'):
                    azure_config['use_ssml'] = settings.azure_use_ssml
                if hasattr(settings, 'azure_device'):
                    azure_config['device'] = settings.azure_device

                self._service = TTSEngine(**azure_config)
            elif provider == 'gcp' or provider == 'google':
                from app.tts_engine.tts_engine_gcp import TTSEngine
                # GCP-specific configuration
                gcp_config = {}
                if hasattr(settings, 'gcp_voice_name'):
                    gcp_config['voice_name'] = settings.gcp_voice_name
                if hasattr(settings, 'gcp_language_code'):
                    gcp_config['language_code'] = settings.gcp_language_code
                if hasattr(settings, 'gcp_sample_rate_hz'):
                    gcp_config['sample_rate_hz'] = settings.gcp_sample_rate_hz
                if hasattr(settings, 'gcp_speaking_rate'):
                    gcp_config['speaking_rate'] = settings.gcp_speaking_rate
                if hasattr(settings, 'gcp_pitch'):
                    gcp_config['pitch'] = settings.gcp_pitch
                if hasattr(settings, 'gcp_volume_gain_db'):
                    gcp_config['volume_gain_db'] = settings.gcp_volume_gain_db
                if hasattr(settings, 'gcp_use_ssml'):
                    gcp_config['use_ssml'] = settings.gcp_use_ssml
                if hasattr(settings, 'gcp_device'):
                    gcp_config['device'] = settings.gcp_device

                self._service = TTSEngine(**gcp_config)
            else:
                raise TTSServiceException(f"Unsupported TTS provider: {provider}")

            self._service.start_service()
            self._is_initialized = True
        except Exception as e:
            raise TTSServiceException(f"Failed to initialize TTS service: {str(e)}")

    def shutdown(self):
        """Shutdown the TTS service."""
        if self._service:
            try:
                self._service.stop_service()
            except Exception:
                pass  # Ignore shutdown errors
            finally:
                self._service = None
                self._is_initialized = False

    def submit_request(self, text: str, custom_filename: Optional[str] = None, language: str = "fi") -> Optional[str]:
        """Submit a TTS request."""
        if not self._is_initialized or not self._service:
            raise TTSServiceException("TTS service not initialized")

        try:
            return self._service.submit_request(text, custom_filename, language)
        except Exception as e:
            raise TTSServiceException(f"Failed to submit TTS request: {str(e)}")

    def get_task_message_queue(self):
        """Get the task message queue for monitoring."""
        if not self._is_initialized or not self._service:
            raise TTSServiceException("TTS service not initialized")

        return self._service.get_task_message_queue()

    def get_queue_size(self):
        """Get the current queue size."""
        if not self._is_initialized or not self._service:
            raise TTSServiceException("TTS service not initialized")

        return self._service.get_queue_size()

    def get_task_message_queue_size(self):
        """Get the current task message queue size."""
        if not self._is_initialized or not self._service:
            raise TTSServiceException("TTS service not initialized")

        return self._service.get_task_message_queue_size()

    def get_device_info(self):
        """Get device information."""
        if not self._is_initialized or not self._service:
            raise TTSServiceException("TTS service not initialized")

        return self._service.get_device_info()

    def switch_device(self, new_device):
        """Switch device (only applicable for local TTS engine)."""
        if not self._is_initialized or not self._service:
            raise TTSServiceException("TTS service not initialized")

        return self._service.switch_device(new_device)

    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._is_initialized
