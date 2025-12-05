"""эндпоинты для проверки состояния сервисов """

from fastapi import APIRouter, Depends
from app.core.dependencies import get_whisper, get_ollama, get_tts
from app.models.schemas import HealthResponse
from app.services.whisper_service import WhisperService
from app.services.ollama_service import OllamaService
from app.services.tts_service import TTSService

router = APIRouter(tags=["состояние"])

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка состояния",
    description="Проверка состояния всех сервисов",
)
async def health_check(
    whisper: WhisperService = Depends(get_whisper),
    ollama: OllamaService = Depends(get_ollama),
    tts: TTSService = Depends(get_tts),
):
    """Проверка состояния всех сервисов"""
    
    ollama_available =  await ollama.is_available()
    tts_available = tts.is_available()
    
    all_healthy = whisper.is_loaded and ollama_available and tts_available
    
    return HealthResponse(
        status = "healthy" if  (whisper)
    )
