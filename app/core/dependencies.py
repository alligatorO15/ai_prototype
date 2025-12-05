"""
DI для FastApi
"""

from app.services.whisper_service import WhisperService, get_whisper_service
from app.services.ollama_service import OllamaService, get_ollama_service
from app.services.tts_service import TTSService, get_tts_service

def get_whisper() -> WhisperService:
    """Зависимость для сервиса Whisper"""
    return get_whisper_service()

def get_ollama() -> OllamaService:
    """Зависимость для сервиса Ollama"""
    return get_ollama_service()

def get_tts() -> TTSService:
    """Зависимость для сервиса TTS"""
    return get_tts_service()