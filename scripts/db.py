from imports.imports import os, dt, logger, pickle, load_dotenv
from imports.imports import create_engine, Table, MetaData, Column, Text, TIMESTAMP, text, insert

load_dotenv()

DB_ASMI = os.getenv("DB_ASMI")
DB_RUS = os.getenv("DB_RUS")
DB_FOREIGN = os.getenv("DB_FOREIGN")
DB_ERROR = os.getenv("DB_ERROR")
DB_TM = os.getenv("DB_TM")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")

# engines for work with project's databases:

# main news databases
asmi = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_ASMI}', pool_pre_ping=True)
# auxiliary news databases
russian = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_RUS}', pool_pre_ping=True)
foreign = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_FOREIGN}', pool_pre_ping=True)
error = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_ERROR}', pool_pre_ping=True)
# archive database, contains news for more than 20 years
time_machine = create_engine(
    f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_TM}', pool_pre_ping=True)


class DataBaseMixin:
    """
    Contains a set of universal functions for working with databases
    Содержит набор универсальных функций для работы с базами данных
    """

    @staticmethod
    def get_table(engine, table_name: str):
        """
        Defines the metadata structure for the table so that you can work with it via ORM
        Определяет структуру метаданных для таблицы, чтобы можно было с ней работать через ORM
        """
        table_small = Table(table_name, MetaData(),
                            Column('url', Text),
                            Column('date', TIMESTAMP),
                            Column('news', Text),
                            Column('links', Text),
                            Column('agency', Text),
                            extend_existing=True,
                            autoload_with=engine)
        table_big = Table(table_name, MetaData(),
                          Column('url', Text),
                          Column('date', TIMESTAMP),
                          Column('title', Text),
                          Column('resume', Text),
                          Column('links', Text),
                          Column('news', Text),
                          Column('category', Text),
                          Column('agency', Text),
                          extend_existing=True,
                          autoload_with=engine)
        return table_small if engine == russian and table_name == 'news' else table_big

    @staticmethod
    def is_not_empty(table_name: str):
        """
        Checks the table for records in it
        Проверяет таблицу на наличие записей в ней
        """
        q = f'SELECT * FROM {table_name} LIMIT 1'
        result = DataBaseMixin.get(q, russian)
        return True if result != [] else False

    @staticmethod
    def get(query: str, engine) -> list[dict]:
        """
        db -> data as a list of dicts

        Accepts a query in the database and returns the result of its execution
        Принимает запрос в БД и возвращает результат его исполнения
        """
        with engine.begin() as conn:
            query_text = text(query)
            result_set = conn.execute(query_text)
            results_as_dict = result_set.mappings().all()
            return results_as_dict

    @staticmethod
    def record(engine, table_name: str, data: list[dict]):
        """
        data -> db.table_name

        Receives a request to write a list of dicts to the database and writes the request
        Принимает запрос на запись списка словарей в БД и производит запись
        """
        try:
            table = DataBaseMixin.get_table(engine, table_name)
            with engine.begin() as conn:
                ins = insert(table)
                conn.execute(ins, data)
            # logger.info(f'В базу {table_name} записано успешно')
        except Exception as e:
            logger.exception(e)
            filename = \
                table_name + \
                '-' + str(dt.datetime.now()).split()[0] + \
                '-' + str(dt.datetime.now()).split()[-1].split('.')[-1]
            with open(f'backups/{filename}.pkl', 'wb') as f:
                pickle.dump(data, f)
            logger.error(e)
        # logger.error(
        # 	f'Отказ записи в {table_name}. Ваши данные сохранены в файл {filename}.pkl. Запишите их вручную')

    @staticmethod
    def erase(table_name: str):
        """
        full.db.table_name - > empty.db.table.name

        Deletes all records from the specified table
        Удаляет все записи из указываемой таблицы
        """
        try:
            table = DataBaseMixin.get_table(russian, table_name)
            with russian.begin() as conn:
                del_query = table.delete()
                conn.execute(del_query)
            logger.info(f'Временная база данных {table_name} очищена')
        except Exception:
            logger.error(f'Ошибка очистки временной базы данных {table_name}. Проведите очистку вручную.\n')

    @staticmethod
    def move(table_from: str, table_to: str, data: list[dict]):
        """
        db.old.is_full, db.new
        db.old - data- > db.new
        db.old.is_empty, db.new.is_full

        Moves data to a new table, clearing the data in the previous table.
        Перемещает данные в новую таблицу, очищая данные в прежней. Сама обработка данных происходит во вне
        """
        engine = russian if table_to == 'final' else asmi
        DataBaseMixin.record(engine, table_to, data)
        DataBaseMixin.erase(table_from)


class Query(DataBaseMixin):
    """
    Contains universal and basic database queries used in the main code
    Содержит универсальные и базовые запросы к базам данных, используемые в основном коде
    """

    @staticmethod
    def get_monocategory_dict() -> dict:
        """
        Builds a dictionary of specialized channels that are providers of only one news category
        Формирует словарь специализированных каналов, которые являются поставщиком только одной категории новостей
        """
        query_mono_category = \
            "SELECT telegram, mono_category FROM agencies WHERE is_parsing = True and not mono_category = 'None'"
        mono_category_alchemy = DataBaseMixin.get(query_mono_category, asmi)
        mono_dict = {el['telegram']: el['mono_category'] for el in mono_category_alchemy}

        return mono_dict

    @staticmethod
    def get_last_news_id() -> dict:
        """
        Builds a dictionary of recent id-news for each agency
        Формирует словарь последних id-новостей для каждого агентства
        """
        last_agencies_url_query = \
            "WITH t1 as (SELECT DISTINCT agency, max(date) OVER (PARTITION BY agency) as date FROM news) " \
            "SELECT t1.agency, url FROM t1 JOIN news USING(date) WHERE t1.agency = news.agency"
        all_active_agencies_query = \
            "SELECT telegram FROM agencies WHERE is_parsing is True"

        last_url_list = DataBaseMixin.get(last_agencies_url_query, asmi)
        all_agencies_list = DataBaseMixin.get(all_active_agencies_query, asmi)

        last_url_dict = {el['agency']: int(el['url'].split('/')[-1]) for el in last_url_list}
        present_smi = [el['telegram'] for el in all_agencies_list]

        result_dict = {}
        for channel_name in present_smi:
            channel_link = 'https://t.me/s/' + channel_name
            if channel_name in last_url_dict:
                result_dict[channel_link] = last_url_dict[channel_name]
            else:
                result_dict[channel_link] = 0
        return result_dict

    @staticmethod
    def get_all_articles_dict(engine) -> dict:
        """
        Builds a dictionary of all existing article id's by each agency
        Формирует словарь всех существующих id статей в разрезе каждого агентства
        """
        base_to = 'final' if engine == russian else 'news'
        all_agencies_articles = {}
        query = f"SELECT agency, url FROM {base_to}"
        query_result = DataBaseMixin.get(query, engine)
        all_articles = [dict(fresh_news) for fresh_news in query_result]

        all_active_agencies_query = "SELECT telegram FROM agencies WHERE is_parsing is True"
        all_agencies_list = DataBaseMixin.get(all_active_agencies_query, asmi)

        for agency in all_agencies_list:
            articles_tuple = tuple(
                el['url'].split('/')[-1] for el in all_articles if el['agency'] == agency['telegram'])
            all_agencies_articles[agency['telegram']] = articles_tuple
        return all_agencies_articles

    @staticmethod
    def get_all_ids(engine, base_to) -> list[dict]:
        """
        Builds a dictionary of all existing article id's
        Формирует словарь всех существующих id статей
        """
        query = f"SELECT agency, split_part(url, '/', 5)::int AS id FROM {base_to}"
        query_result = DataBaseMixin.get(query, engine)
        return query_result
