from sqlalchemy import Column, Integer, String, Text, DateTime #Для определения структуры таблицы
from sqlalchemy.sql import func #Для .now()
from database import Base #Для декларативного определения моделей


class Translation(Base): #Определение модели
    __tablename__ = "translations" #Созданиие таблицы в БД
    #Поля таблицы
    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=False)
    adaptation_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())