from sqlalchemy import create_engine #Для подключения к БД
from sqlalchemy.ext.declarative import declarative_base #Базовый класс для моделей
from sqlalchemy.orm import sessionmaker #Для создания фабрики сессий
from config import settings


engine = create_engine(settings.database_url) #создание движка
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #создания фабрики сессий
Base = declarative_base() #создание базового класса для всех моделей

def get_db(): # создает сессии при каждом HTTP запросе
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()