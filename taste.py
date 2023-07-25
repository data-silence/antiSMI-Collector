from db import *
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum
# from typing import Optional


class ShortNewsFields(BaseModel):
    """Класс для валидации полей временной таблицы news"""
    url: HttpUrl
    date: dt.datetime
    news: str = Field(..., min_length=1)  # отсеваем пустые столбцы
    links: HttpUrl
    agency: str

    class Config:
        orm_mode = True


class ShortModel(BaseModel):
    """Класс для валидации списка новостей, который будет записан во временную таблицу news"""
    dicts_list: list[ShortNewsFields]


class CategoryEnum(str, Enum):
    economy = 'economy'
    science = 'science'
    sports = 'sports'
    technology = 'technology'
    entertainment = 'entertainment'
    society = 'society'


class AsmiFields(BaseModel):
    """Класс для валидации полей временной таблицы news"""
    url: HttpUrl
    date: dt.datetime
    title: str
    resume: str
    category: CategoryEnum
    news: str = Field(..., min_length=1)  # отсеваем пустые столбцы, '...' - required
    links: HttpUrl
    agency: str

    class Config:
        orm_mode = True


class AsmiModel(BaseModel):
    """Класс для валидации списка новостей, который будет записан во временную таблицу news"""
    dicts_list: list[AsmiFields]


def validate_and_write_to_news_db(news_list: list[ShortNewsFields]) -> int:
    try:
        validator_model = ShortModel(dicts_list=news_list)
        DataBaseMixin.record(smi, 'news', news_list)
        len_news = len(news_list)
    except ValueError:
        record_list = []
        error_list = []
        for news in news_list:
            try:
                validator_fields = ShortNewsFields(**news)
                record_list.append(news)
            except ValueError:
                logger.error(news)
                error_list.append(news)
        DataBaseMixin.record(smi, 'news', record_list)
        DataBaseMixin.record(smi, 'error_table', error_list)
        len_news = len(record_list)
    return len_news


def validate_and_write_to_asmi(news_list: list[AsmiFields]):
    try:
        validator_model = AsmiModel(dicts_list=news_list)
        DataBaseMixin.move('final', 'news', news_list)
        len_news = len(news_list)
    except ValueError:
        record_list = []
        for news in news_list:
            try:
                validator_fields = AsmiFields(**news)
                record_list.append(news)
            except ValueError:
                logger.error(news)
        DataBaseMixin.move('final', 'news', record_list)
        len_news = len(record_list)
    return len_news
