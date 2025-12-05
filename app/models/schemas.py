"""
Pydantic модели для запросов и ответов нашего Апи
"""

from typing import Optional 
from pydantic import BaseModel,Field


class TranscriptionResult(BaseModel):
    """Результат распознавания речи"""
    
    text: str = Field(..., description="Распознанный текст из аудио-файла")
    language: str = Field(default="ru",description="Язык")
    duration: float = Field(..., description="Длительность аудио в сек.")
    
    
class LLMResponse(BaseModel):
    """Ответ от LLM"""
    
    response:str = Field(..., description="Сгененрированный текст ответа")
    model: str = Field(..., description="Используемая модель")
    
    
class VoiceAssistantRequest(BaseModel):
    """Параметры запроса к голосовому ассистенту"""
    
    generate_audio: bool = Field(default=True, description="Надо ли генерировать аудио-ответ")
    system_prompt: Optional[str] = Field(default=None, description="Польовательский сиситемный промпт")
    
    
class VoiceAssistantResponse(BaseModel):
    """Ответ от голосового ассистента"""
    
    transcription: str = Field(...,description="Распознанная речь пользователя")
    llm_response: str = Field(..., description="Ответ от LLM")
    audio_url: Optional[str] = Field(default=None, description="URL сгенерированного аудио ответа")
    processing_time: float = Field(..., description="Общее время обработки в секундах")
    
class HealthResponse(BaseModel):
    """Ответ проверки состояния сервера"""
    
    status: str = Field(default="healthy")
    whisper_loaded: bool = Field(default=False)
    ollama_available: bool = Field(default=False)
    tts_available: bool = Field(default=True)
    
class ErrorResponse(BaseModel):
    """Ответ в случае ошибки"""
    
    error: str = Field(..., description="Сообщение об ощибке")
    details: Optional[str] = Field(default=None, description="Детали об ошибке")