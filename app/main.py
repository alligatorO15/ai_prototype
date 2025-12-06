"""
Голосовой AI-ассистент.
Пайплайн: распознавание речи, обработка и ответ LLM, синтез речи(опционально).
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings
from app.api.routes import voice,health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
   
    settings = get_settings()
    logger.info(f"Запуск {settings.app_name}...")
    
    
    if not settings.debug:
        try:
            from app.services.whisper_service import get_whisper_service
            logger.info("Предзагрузка модели Whisper...")
            get_whisper_service()
            logger.info("Модель whisper успешно загружена")
        except Exception as e:
            logger.warning(f"Не удалось предзагрузить модель Whisper: {e}")
    
    logger.info(f"{settings.app_name} успешно запущен")
    
    yield
    
 
    logger.info(f"Завершение работы {settings.app_name}...")
    
    # Очистка старых  файлов
    try:
        from app.services.tts_service import get_tts_service
        tts = get_tts_service()
        tts.cleanup_old_files(max_age_hours=1)
    except Exception:
        pass
    
    logger.info("Завершение работы выполнено")


def create_app() -> FastAPI:
    """Создание и настройка FastAPI приложения."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="""
## API голосового AI-ассистента

Полный пайплайн голосового ассистента:
- Приём аудиофайлов WAV
- Распознавание речи с помощью Whisper (faster-whisper)
- Генерация ответов через Ollama LLM
- Синтез речи с помощью gTTS

### Эндпоинты

- **POST /voice/process** — Полный пайплайн голосового ассистента
- **POST /voice/transcribe** — Только распознавание речи
- **POST /voice/generate** — Только генерация текста LLM
- **POST /voice/synthesize** — Только синтез речи
- **GET /health** — Проверка состояния сервисов
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    
    # Подключение маршрутов
    app.include_router(health.router)
    app.include_router(voice.router)
    
    return app

app = create_app()

#этотт код запуститься толко когда файл станет исполняемым(при команде python app/main.py). Docker использует uvicorn напрямую
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
