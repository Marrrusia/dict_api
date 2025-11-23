from pydantic_settings import BaseSettings #Для управления конфигурацией в приложениях


class Settings(BaseSettings):
    database_url: str = "sqlite:///./translations.db" # Конфигурация базы данных

    llm_api_url: str = "http://localhost:11434/api/generate" # Конфигурация LLM
    llm_model: str = "gemma2:2b"

    app_host: str = "0.0.0.0" #Настройки веб-сервера FastAPI
    app_port: int = 8000
    debug: bool = True


settings = Settings()


