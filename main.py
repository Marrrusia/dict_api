from fastapi import FastAPI, Depends, HTTPException, Request, Query #Для работы с fastapi
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session #Для работы с БД
from typing import List, Optional #Типизация и валидация
from pydantic import BaseModel, Field, field_validator

from database import get_db, engine
from llm_service import LLMService
import models

models.Base.metadata.create_all(bind=engine) #Создание таблиц

app = FastAPI( #Инициализация FastAPI приложения
    title="Переводчик",
    description="Сервис перевода текстов с использованием LLM"
)

app.mount("/static", StaticFiles(directory="static"), name="static") #для js и css
templates = Jinja2Templates(directory="templates") #для html

llm_service = LLMService() #Создание экземпляра сервиса переводов

# Список поддерживаемых языков
SUPPORTED_LANGUAGES = ["ru", "en", "es", "fr", "de", "it", "zh", "ja", "ko", "ar", "pt", "auto"]
SUPPORTED_TARGET_LANGUAGES = ["ru", "en", "es", "fr", "de", "it", "zh", "ja", "ko", "ar", "pt"]


class TranslationRequest(BaseModel): #модель запроса
    text: str = Field(..., description="Текст для перевода", json_schema_extra={"example": "Hello world"})
    source_lang: str = Field(..., description="Исходный язык", json_schema_extra={"example": "en"})
    target_lang: str = Field(..., description="Целевой язык", json_schema_extra={"example": "ru"})
    adaptation_type: Optional[str] = Field(None, description="Стиль перевода", json_schema_extra={"example": "casual"})

    #Добавлена валидация для исключения возможности ввода неизвестных языков
    @field_validator('source_lang')
    @classmethod
    def validate_source_lang(cls, v):
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Неподдерживаемый исходный язык. Доступные: {', '.join(SUPPORTED_LANGUAGES)}")
        return v

    @field_validator('target_lang')
    @classmethod
    def validate_target_lang(cls, v):
        if v not in SUPPORTED_TARGET_LANGUAGES:
            raise ValueError(f"Неподдерживаемый целевой язык. Доступные: {', '.join(SUPPORTED_TARGET_LANGUAGES)}")
        return v


class TranslationResponse(BaseModel): #модель ответа
    id: int = Field(..., description="ID перевода в базе данных")
    original_text: str = Field(..., description="Оригинальный текст")
    source_lang: str = Field(..., description="Исходный язык")
    target_lang: str = Field(..., description="Целевой язык")
    translated_text: str = Field(..., description="Переведенный текст")
    adaptation_type: Optional[str] = Field(None, description="Стиль перевода")
    created_at: str = Field(..., description="Время создания")


@app.get("/", tags=["Веб-интерфейс"],response_class=HTMLResponse,         #HTML интерфейс
         summary="Главная страница",
         description="Возвращает веб-интерфейс для работы с сервисом перевода" )
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/translate", tags=["Реализация переводчика"],
          response_model=TranslationResponse,summary="Выполнить перевод текста",
          description="Переводит текст с одного языка на другой с использованием LLM",
          responses={
              200: {"description": "Успешный перевод"},
              400: {"description": "Неверный запрос"},
              500: {"description": "Ошибка сервера"}
          }
          )
async def translate_text(request: TranslationRequest, db: Session = Depends(get_db)):
    try: #Поиск существующего перевода
        existing_translation = db.query(models.Translation) \
            .filter(
            models.Translation.original_text == request.text,
            models.Translation.source_lang == request.source_lang,
            models.Translation.target_lang == request.target_lang,
            models.Translation.adaptation_type == request.adaptation_type
        ) \
            .order_by(models.Translation.created_at.desc()) \
            .first()

        if existing_translation: #использование существующей записи
            db_translation = existing_translation
        else: #создание новой записи
            translated_text = await llm_service.translate_text(
                text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                adaptation_type=request.adaptation_type
            )

            db_translation = models.Translation(
                original_text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                translated_text=translated_text,
                adaptation_type=request.adaptation_type
            )
            db.add(db_translation)

        db.commit() #сохранение изменений в БД
        db.refresh(db_translation) #перезагрузка БД
        # Формирование ответа
        return TranslationResponse(
            id=db_translation.id,
            original_text=db_translation.original_text,
            source_lang=db_translation.source_lang,
            target_lang=db_translation.target_lang,
            translated_text=db_translation.translated_text,
            adaptation_type=db_translation.adaptation_type,
            created_at=db_translation.created_at.isoformat()
        )
    # Анализ ошибок
    except Exception as e:
        db.rollback()
        if "LLM API error" in str(e):
            raise HTTPException(status_code=500, detail="Ошибка подключения к сервису перевода.")
        elif "Translation failed" in str(e):
            raise HTTPException(status_code=500, detail="Ошибка при выполнении перевода. Попробуйте еще раз.")
        else:
            raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@app.get("/history/translations", tags=["Реализация переводчика"],
         response_model=List[TranslationResponse], summary="История переводов",
         description="Возвращает историю выполненных переводов из базы данных",
         responses={
             200: {"description": "Успешное получение истории"},
             500: {"description": "Ошибка базы данных"}
         }
         )
async def get_translation_history(
        skip: int = Query(0, description="Количество записей для пропуска", ge=0),
        limit: int = Query(100, description="Максимальное количество записей", ge=1, le=100),
        db: Session = Depends(get_db)
):
    try: #Создает объект запроса SQLAlchemy (Translation таблица с которой работаем). С сортировкой по добавлению. Ограничевает колличество возвращаемых записей
        translations = db.query(models.Translation) \
            .order_by(models.Translation.created_at.desc()) \
            .offset(skip) \
            .limit(limit) \
            .all() #выполнение запроса в базе данных

        result = []
        for t in translations: #Итерация по данным
            response = TranslationResponse(
                id=t.id,
                original_text=t.original_text,
                source_lang=t.source_lang,
                target_lang=t.target_lang,
                translated_text=t.translated_text,
                adaptation_type=t.adaptation_type,
                created_at=t.created_at.isoformat()
            )
            result.append(response)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при загрузке истории переводов")


# Эндпоинт для очистки БД
@app.delete("/clear", tags=["Вспомогательные инструменты"], summary="Очистка базы данных")
async def clear_database(db: Session = Depends(get_db)):
    try:
        count = db.query(models.Translation).count()  # Подсчет записей
        db.query(models.Translation).delete()         # Удаление всех записей
        db.commit()                                   # Подтверждение
        return {"message": f"База очищена. Удалено {count} записей"}
    except Exception as e:
        db.rollback()                                 #Откат при ошибке
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")