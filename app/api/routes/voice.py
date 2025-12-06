"""Эндпоинты для обработки голосовых запросов"""

import logging
import time
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from app.config import get_settings
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
    system_prompt: Optional[str] = Form(default = None, description = "Пользовательский системный промпт"),
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
    
    if not audio.filename or not audio.filename.lower().endswith(SUPPORTED_AUDIO_FORMATS):
        raise HTTPException(
            status_code=400,
            detail = f"Неподдерживаемый формат аудио. Поддерживаются {', '.join(SUPPORTED_AUDIO_FORMATS)}",
        )
        
    audio.file.seek(0,2)
    file_size = audio.file.tell()#чтобы не читать весь файл в память
    audio.file.seek(0)
    
    if file_size > settings.max_file_size *1024 *1024:
        raise HTTPException(
            status_code = 400,
            detail = f"Файл слишком большой. Максимальный размер: {settings.max_file_size} Mб"
        )
        
    settings.upload_dir.mkdir(parents = True, exist_ok = True)
    file_suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    temp_path = settings.upload_dir / f"temp_{uuid.uuid4().hex}{file_suffix}" #потому что faster-whisper работает с файлом на диске, а не с переданными байтами в памяти.
    
    try:
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
            
        try:
            text,language,duration = whisper.transcribe(temp_path)
            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="В аудиофайле нет речи"
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка распознавания: {e}")
        
        logger.info(f"Распознанный текст из аудиофайла: {text}")
        
        try:
            llm_response = await ollama.chat(
                user_message=text,
                system_prompt=system_prompt
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка генерации ответа LLM: {e}"
            )
            
        logger.info(f"Ответ LLM: {llm_response[:100]}...")
        
        audio_url = None
        if generate_audio and settings.tts_enabled:
            try:
                audio_filename = f"response_{uuid.uuid4().hex[:8]}.mp3"
                audio_path = tts.synthesize(
                    text=llm_response,
                    language=language or 'ru',
                    filename=audio_filename
                )
                logger.info(f"Путь к аудиофайлу после преобразования TTS: {audio_path}")
                
                audio_url = f"/voice/audio/{audio_filename}"
            except Exception as e:
                logger.error(f"Ошибка синтеза речи: {e}")
        
        processing_time = time.time() - start_time
        
        return VoiceAssistantResponse(
            transcription=text,
            llm_response=llm_response,
            audio_url=audio_url,
            processing_time=round(processing_time,2)
        )
            
    finally:
        if temp_path.exists():
            temp_path.unlink()
            
            
@router.post(
    "/transcribe",
    response_model=TranscriptionResult,
    summary="Распознавание речи",
    description="Загрузите аудиофайл и получите текстовую расшифровку",
)
async def transcribe_audio(
    audio: UploadFile = File(..., description="Аудиофайл для распознавания"),
    language: Optional[str] = Form(default=None, description="Код языка. Если не указан, то автопределение"),
    whisper: WhisperService = Depends(get_whisper),
):
    "Только преобразование речи из аудиофайла в текст через Whisper"
    
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    file_suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    temp_path= settings.upload_dir / f"temp_{uuid.uuid4().hex}{file_suffix}"
    
    try:
        with open(temp_path,"wb") as f:
            content = await audio.read()
            f.write(content)
            
        text, detected_lang, duration = whisper.transcribe(temp_path, language=language)
        
        return TranscriptionResult(
            text=text,
            language=detected_lang,
            duration=round(duration,2)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка распознавания: {e}"
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()
            
@router.post(
    "/generate",
    response_model=LLMResponse,
    summary="Генерация ответа LLM",
    description="Отправьте текст в LLM и получите ответ",
)
async def generate_response(
    text: str = Form(..., description="Текстовый запрос для LLM"),
    system_prompt: Optional[str] = Form(default=None, description="Пользовательский системный промпт"),
    ollama: OllamaService = Depends(get_ollama),
):
    """Генерация ответа LLM"""
    settings = get_settings()
    
    try:
        response = await ollama.chat(
            user_message=text,
            system_prompt=system_prompt
        )
        
        return LLMResponse(
            response=response,
            model=settings.ollama_model
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка генерации ответа LLM{e}"
        )
        
        
@router.post(
    "/synthesize",
    summary="Синтез речи",
    description="Преобразование текста в речь и возврат аудиофайла",
)
async def synthesize_speech(
    text: str = Form(..., description="Текст для преобразования в речь"),
    language: str = Form(default="ru", description="Код языка"),
    tts: TTSService = Depends(get_tts)
):
    """Преобразование текста в речь"""
    try:
        audio_path = tts.synthesize(text=text, language=language)
        return FileResponse(
            path=str(audio_path),
            media_type="audio/mpeg",
            filename=audio_path.name
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка синтеза речи: {e}"
        )
        

@router.get(
    "/audio/{filename}",
    summary="Получение аудиофайла",
    description="Получение сгенерирвоанного аудиофайла по имени",
)
async def get_audio(filename: str):
    """Получение сгенерированного аудиофайла"""
    settings= get_settings()
    audio_path = settings.output_dir / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Аудиофайл не найден")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename   
    )
 

