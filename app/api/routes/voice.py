"""Эндпоинты для обработки голосовых запросов"""

import logging
import time
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.config import get_settigs
from app.core.dependencies import get_ollama, get_tts, get_whisper
from app.models.schemas import (
    VoiceAssistantResponse,
    LLMResponse,
    TranscriptionResult,
    ErrorResponse,
)
from app.services.whisper_service import WhisperService
from app.services.ollama_service import OllamaService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice",tags=["Голосовой ассистент"])
SUPPORTED_AUDIO_FORMATS = ('.wav') #можно потом добавить и другие('.wav','.mp3','.ogg' и т.д.)

@router.post(
    "/process",
    response_model=VoiceAssistantResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Неверный запрос"},
        500: {"model": ErrorResponse, "description": "Ошибка обработк(со стороны сервера)"}
    },
    summary="Обработка голосового сообщения",
    description="Загрузитке wav аудиофайл ==> текст распознанной речи, ответ LLM и сгенерированный аудиоответ(опционально)",
)
async def process_voice(
    audio: UploadFile = File(..., description="Аудиофайл WAV"),
    generate_audio: bool = Form(default=True, description = "Надо ли генерировать аудиоответ"),
    system_prompt: bool = Form(default = None, description = "Пользовательский системный промпт"),
    whisper: WhisperService = Depends(get_whisper),
    ollama: OllamaService = Depends(get_ollama),
    tts: TTSService = Depends(get_tts),
):
    """
    Полный пайплайн голосового ассистента:
    1. Приём аудиофайла WAV
    2. Распознавание речи в текст (Whisper)
    3. Генерация ответа (Ollama LLM)
    4. Синтез аудио ответа (gTTS) — опционально
    """
    
    start_time = time.time()
    settings = get_settings()
    
    if not audio.filename.lower().endwith(SUPPORTED_AUDIO_FORMATS):
        raise HTTPException(
            status_code=400,
            detail = f"Неподдерживаемый формат аудио. Поддерживаются {', '.join(SUPPORTED_AUDIO_FORMATS)}",
        )
        
    audio.file.seek(0,2)
    file_size = audio.file.tell()#чтобы не читать весь файл в память
    audio.file.seek(0)
    
    if file_size > settings.max_file_size *1024 *1024:
        raise HTTPException(
            statuse_code = 400,
            detail = f"Файл слишком большой. Максимальный размер: {settings.max_file_size} Mб"
        )
        
    settings.upload_dir.mkdir(parents = True, exist_ok = True)
    temp_path = settings.upload_dir / f"temp_{uuid.uuid4().hex}{Path(audio.filename).suffix}" #потому что faster-whisper работает с файлом на диске, а не с переданными байтами в памяти.
    
    try:
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
            
        try:
            text,language,duration = whisper.transcribe(temp_path)
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Речь в аудиофайле нет."
                )
        except Run
 

