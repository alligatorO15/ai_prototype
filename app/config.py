from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения. Загружаются из переменных окружения
    """
    app_name:str = 'Голосовой AI-ассистент'
    debug: bool = False

    whisper_model_size: str = 'base'
    whisper_device: str = 'auto'
    whisper_compute_type: str = 'auto'


    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout: int = 120

    tts_enabled: bool = True
    tts_language: str = "ru"
    
    upload_dir: Path = Path("uploads")
    output_dir: Path = Path("outputs")
    max_file_size: int = 25
    
    system_prompt: str = """Ты вежливы и полезный AI-ассистент. Отвечай на русском, кратко и по существу. Будь вежливым"""
    
@lru_cache
def get_settings() -> Settings:
    """Получаем кэшируемый экземпляр настроек с помощью декоратора lru_cache"""
    return Settings()
     