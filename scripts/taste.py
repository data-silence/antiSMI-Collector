from imports.imports import dt, logger, BaseModel, HttpUrl, Field, Enum

from scripts.db import DataBaseMixin, smi
from scripts.cook import erase_folder

'''
This module is a validator: all data fields are checked and the news is written to the databases in case of success
Depending on the validation stage, validation can be preliminary (ShortModel) or final (asmiModel)

Модуль представляет собой валидатор: проверяются все поля данных новости, и в случае успеха производится запись в БД
В зависимости от стадии валидации проверка может быть предварительной (ShortModel) или финальной (asmiModel)
'''


class ShortNewsFields(BaseModel):
    """
    Class for validating fields of the temporary table news
    Класс для валидации полей временной таблицы news
    """
    url: HttpUrl
    date: dt.datetime
    news: str = Field(..., min_length=1)  # отсеваем пустые столбцы
    links: HttpUrl
    agency: str

    class Config:
        orm_mode = True


class ShortModel(BaseModel):
    """
    A class to validate the list of news that will be written to the temporary news table
    Класс для валидации списка новостей, который будет записан во временную таблицу news
    """
    dicts_list: list[ShortNewsFields]


class CategoryEnum(str, Enum):
    """
    Class to check if it belongs to the used categories
    Класс для проверки на принадлежность используемым категориям
    """
    economy = 'economy'
    science = 'science'
    sports = 'sports'
    technology = 'technology'
    entertainment = 'entertainment'
    society = 'society'


class AsmiFields(BaseModel):
    """
    Field validation class for writing to the antiSMI database
    Класс валидации полей для записи в базу данных antiSMI
    """
    url: HttpUrl
    date: dt.datetime
    title: str
    resume: str
    category: CategoryEnum
    # clear the empty columns
    # убираем пустые столбцы
    news: str = Field(..., min_length=1)  # "'...' - required
    links: HttpUrl
    agency: str

    class Config:
        orm_mode = True


class AsmiModel(BaseModel):
    """
    Class for validating the list of news to be written to the antiSMI database
    Класс для валидации списка новостей, который будет записан в базу данных antiSMI
    """
    dicts_list: list[AsmiFields]


def validate_and_write_to_news_db(news_list: list[ShortNewsFields]) -> int:
    """
    Basic function for validating and writing news to temporary databases
    Основная функция для валидации и записи новостей во временные базы данных
    """
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
    """
    Basic function for validating and writing news to antiSMI database
    Основная функция для валидации и записи новостей в базу данных antiSMI
    """
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


def check_and_move_to_asmi():
    """
    Orchestration function | Окестрирующая функция
    final.db news -> validator -> antiSMI.db
    """
    q = 'select * from final'
    final_news = DataBaseMixin.get(q, smi)
    if len(final_news):
        try:
            len_news = validate_and_write_to_asmi(final_news)
            logger.info(f'Успешно записано {len_news} новостей\n')
            erase_folder('pkl')
        except Exception as e:
            logger.exception(f'Не смог обработать из-за ошибки {e}\n')
