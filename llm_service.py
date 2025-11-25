import httpx #Для отправки запросов к Ollama
from typing import Optional
from config import settings


class LLMService:
    def __init__(self):
        self.api_url = settings.llm_api_url #эндпоинта Ollama
        self.model = settings.llm_model #определяет модель

        #Словарь языков
        self.language_names = {
            "auto": "auto",
            "ru": "Russian",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "pt": "Portuguese",
        }

    async def translate_text( self, text: str, source_lang: str, target_lang: str, adaptation_type: Optional[str] = None ) -> str:

        prompt = self._build_prompt(text, source_lang, target_lang, adaptation_type) #Построение промпта

        try:
                request_data = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                    }
                }

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(self.api_url, json=request_data)

                if response.status_code == 200:
                    result = response.json()
                    translated_text = result["response"].strip() #извлечение сгенерированного текста
                    return self._clean_response(translated_text)
                else: #Генерация исключения при ошибке
                    raise Exception(f"Ошибка API: {response.status_code}")

        except Exception as e: #Обработка исключения
            raise Exception(f"Перевод не удался: {str(e)}")

    def _build_prompt(self, text: str, source_lang: str, target_lang: str, adaptation_type: Optional[str] = None) -> str:

        source_name = self.language_names.get(source_lang, source_lang)
        target_name = self.language_names.get(target_lang, target_lang)

        # Все написано на английском для повышения точности перевода.
        # Инструкция дополнена требованиями, для исключения вывода не только переведенного текста

        style_instructions = {  #Для выбора стиля перевода
            "casual": "Use casual, everyday language",
            "formal": "Use formal, professional language",
            "marketing": "Use persuasive, engaging marketing style",
            "technical": "Use precise, technical language"
        }

        style_note = style_instructions.get(adaptation_type, "")

        return f"""<start_of_turn>user
Translate the following text from {source_name} to {target_name}. {style_note}
insruction: output only the translated text, don't add any explanations do not write "Translation:" or similar prefixes, 
do NOT include the original text, the output must be pure {target_name} text only

Text: "{text}"<end_of_turn>
<start_of_turn>model
"""


    def _clean_response(self, text: str) -> str: #Проверка что модель не вернула пустую строку
        if not text:
            return "Перевод не удался"
        return text
