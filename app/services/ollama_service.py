"""Cервис для взаимодействия с Ollama LLM"""

import logging 
from typing import Optional
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
_ollama_service: Optional["OllamaService"] = None

class OllamaService:
    """
    Сревис для работы с Ollama LLM
    """
    
    def __init__(self):
        """Инициализация сервиса Ollama"""
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url
        self.model = self.settings.ollama_model
        self.timeout = self.settings.ollama_timeout
        
    async def chat(self, user_message: str, system_prompt: Optional[str] = None,) -> str:
        """запрос к Ollama LLM. Возвращает сгенерированный ответ текста"""
        
        if system_prompt is None:
            system_prompt = self.settings.system_prompt
            
        message = [
            {"role": "system",
             "content": system_prompt},
            {"role": "user",
             "content": user_message},
        ]
        
        logger.info(f"Отправка сообщения  в Ollama")
        
        payload = {
            "model": self.model,
            "messages": message,
            "stream": False,#чтобы фул ответ а не по частям
            "options": {
                "temperature": 0.7,#креативность
                "top_p": 0.9,#выбор токенов по вероятности(из документации Cumulative probability threshold for nucleus sampling)
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                result=response.json()
                generate_text = result.get("message", {}).get("content", "")
                
                logger.info(f"Ответ LLM успешно сгенерирован: {generate_text}[:100]...")
                return generate_text
            
        except httpx.TimeoutException:
            logger.error("Превышено время ожидания чата Ollama")
            raise RuntimeError("Превышено время ожидания чата Ollama")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка чата Ollama: {e}")
            raise RuntimeError(f"HTTP ошибка чата Ollama: {e}")
        except Exception as e:
            logger.error(f"Ошибка чата Ollama {e}")
            raise
        
    async def is_available(self) -> bool:
        """Проверка состояния. Если смогли получить список моделей то работает"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response= await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
            
def get_ollama_service() -> OllamaService:
    """Для создания или получения 1 и того же экземпляра сервисма Ollama"""
             
    global _ollama_service
    if _ollama_service is None:
        _ollama_service=OllamaService()
    return _ollama_service