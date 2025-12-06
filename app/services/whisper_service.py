import logging
from pathlib import Path 
from typing import Optional
from faster_whisper import WhisperModel
from app.config import get_settings

logger=logging.getLogger(__name__)
_whisper_service: Optional[WhisperModel] = None

class WhisperService:
    """
    Сервис для преобразования речи в текст с помощью faster_service
  
    """
    
    _instance: Optional["WhisperService"]=None #Форвардссылка так как на тот момент когда читает строку  класс еще не созд
    _model: Optional[WhisperModel] = None
    
    def __new__(cls) -> "WhisperService":
        """Синглтон паттерн так как модель whisper очень тяжелая.
        Чтобы при Whisper() возвращался 1 и тот же экземпляр"""
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация Whisper-сервера"""
        
        if self._model is None:
            self._load_model()
            
    def _load_model(self) -> None:
        """Загружаем whisper"""
        settings = get_settings()
        
        logger.info(f"Загружаем модель Whisper: {settings.whisper_model_size}, работает на {settings.whisper_device}")
        
        try:
            self._model=WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
            logger.info("модель Whisper загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модел  Whisper: {e}")
            raise
        
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> tuple[str,str,float]:
        """Преобразование аудио файла в текст
        возвращает кортеж(распознанный текст, определение языка, длительность)
        """
        if self._model is None:
            raise RuntimeError("Модель Whisper не загружена")
        
        logger.info(f"Переводим аудио: {audio_path}")
        
        try:
            segments, info =self._model.transcribe(
                str(audio_path),
                language = language,
                beam_size = 5,#что-то про лучевой поиск(чем больше тем точнее, но медленнее)
                vad_filter = True, #фильтровать шум и тищину
                vad_parameters={"min_silence_duration_ms": 500}, # интервал в мс, превысив который распознает как паузу
            )
            
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            full_text=" ".join(text_parts)
            
            return full_text, info.language, info.duration
        except Exception as e:
            logger.error(f"Ошибка распознавания речи: {e}")
            raise
    
    @property
    def is_loaded(self) -> bool:
        return self._model is not None
    
def get_whisper_service() -> WhisperService:
    """Для создания или получения 1 и того же экземпляра Whisper. 
    Тоже как синглтон паттерн контролирует чтобы был 1 экземпляр. 
    Именно этот метод будем использовать для DI"""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service