"""Синтез речи через gTTS"""

import logging
import uuid
from pathlib import Path
from typing import Optional
from gtts import gTTS
from app.config import get_settings

logger=logging.getLogger(__name__)
_tts_service: Optional["TTSService"] = None

class TTSService:
    """Сервис преобразования текста в речь через gTTS"""
    
    def __init__(self):
        self.settings = get_settings()
        self.output_dir = self.settings.output_dir
        self.language = self.settings.tts_language
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Path:
        """Преобразование текста в речь и сохранение в MP3 файл.
        Возвращает путь к сгенерированному файлу.
        """
        
        if language is None:
            language = self.language
            
        if filename is None:
            filename = f"tts_{uuid.uiid4().hex[:8]}.mp3"
            
        output_path = self.output_dir / filename
        
        logger.info(f"Синтез речи. Язык: {language}")
        
        try:
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(output_path))
            logger.info(f"Аудио сохранено: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Ошибка синтеза речи через gTTS:{e}")
            raise
    
    def cleanup_old_files(self, max_age_hours: int = 1) -> int:
        """ Удаление старых сгенерированных аудио файлов. 
        Файлы, время последнего изменнеия которых больше 
        max_age_hours удаляются"""
        
        import time
        
        removed = 0
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        for file in self.output_dir.glob("tts_*.mp3"):
            try:
                if current_time-file.stat().st_mtime > max_age_seconds:
                    file.unlink()
                    removed+=1
            except Exception as e:
                logger.info(f"Ошибка удаления файла {file.name}:{e}")
                
        if removed>0: logger.info(f"Удалено {removed} старых аудио файлов")
        
        return removed
    
    @staticmethod
    def is_available() -> bool:
        """Проверка доступности сервиса TTS(нужен интернет)."""
        
        try:
            import socket
            socket.create_connection(("translate.google.com", 443), timeout=3)
            return True
        except (socket.timeout,socket.error):
            return False
        
def get_tts_service() -> TTSService:
    """Для создания или получения 1 и того же экземпляра сервиса TTS"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
        
            

