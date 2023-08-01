from imports_cook import *
from taste import *
from imports_common import *

logger.add('debugging//debug_cook.json', format="{time} {message}", level='INFO', rotation="1 week", compression="zip",
           serialize=True)


def article2resume(article_text: str) -> str:
    """Делает резюме новости с помощью модели mbart"""
    input_ids = tokenizer_resume(
        [article_text],
        max_length=600,
        padding="max_length",
        truncation=True,
        return_tensors="pt")["input_ids"]

    output_ids = model_resume.generate(
        input_ids=input_ids,
        no_repeat_ngram_size=4)[0]

    summary = tokenizer_resume.decode(output_ids, skip_special_tokens=True)

    return summary


def article2title(summary: str) -> str:
    """Делает заголовок из резюме с помощью модели ruT5"""
    input_ids = tokenizer_title(
        [summary],
        max_length=600,
        add_special_tokens=True,
        padding="max_length",
        truncation=True,
        return_tensors="pt")["input_ids"]

    output_ids = model_title.generate(
        input_ids=input_ids,
        no_repeat_ngram_size=4)[0]

    title = tokenizer_title.decode(output_ids, skip_special_tokens=True)

    return title


def make_full_fresh_news_list() -> list:
    """Забирает свежие новости из smi, получает из них резюме и формирует словарь свежих новостей для записи во
    вспомогательную базу данных smi"""

    if not DataBaseMixin.is_not_empty('news'):
        logger.error(
            f'Обработка новостей не может начаться, так как новости ещё не собраны')
        logger.info('Соберите новости с помощью модуля parse')

    mono_dict = Query.get_monocategory_dict()
    all_fresh_news_query = "SELECT * FROM news"
    all_fresh_news_alchemy = DataBaseMixin.get(all_fresh_news_query, smi)
    fresh_news_list = [dict(fresh_news) for fresh_news in all_fresh_news_alchemy if 'url' in dict(fresh_news).keys()]

    start_t = dt.datetime.now()
    logger.info(f'Начинается обработка новостей от {start_t}:')

    for news in fresh_news_list:
        start_time = dt.datetime.now()
        news['category'] = mono_dict[news['agency']] if news['agency'] in mono_dict.keys() else \
            model_class.predict(news['news'])[0][0].split('__')[-1]
        if news['category'] != 'other' and news['category'] != 'not_news':
            news['title'] = article2title(news['news'])
            news['resume'] = article2resume(news['news'])
            duration = (dt.datetime.now() - start_time).seconds
            logger_dict = {'duration': duration, 'url': news["url"]}
            logger.info(logger_dict)
        else:
            pass
        # logger.error(f'{news["url"]} - не является новостью')
    fixed_news = [news for news in fresh_news_list if news['category'] != 'other' and news['category'] != 'not_news']
    result_time = dt.datetime.now() - start_t
    logger.error(f'{len(fresh_news_list) - len(fixed_news)} отнесены с неновостным сообщениям и не были обработаны')
    logger.info(f'Обработка {len(fixed_news)} новостей завершена за {round(result_time.seconds / 60, 2)} минут')
    logger.info(
        f'Среднее время обработки одной новости: {round(result_time.seconds / (len(fixed_news) + 0.01), 2)} сек')

    return fixed_news


def erase_folder(folder_name: str):
    """Очищает все файлы в заданной папке"""
    for path in Path(folder_name).glob('*'):
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()


def cook_and_move_to_smi():
    """Генерирует резюме и заголовок к свежим новостям, записывает их в базу final для проведения финальной валидации"""
    fresh_news_list = make_full_fresh_news_list()
    if len(fresh_news_list):
        try:
            DataBaseMixin.move('news', 'final', fresh_news_list)
        except Exception as e:
            logger.exception(f'Причина ошибки: {e}')
            filename = \
                str(dt.datetime.now()).split()[0] + '-' + str(dt.datetime.now()).split()[-1].split('.')[-1]
            with open(f'pkl/{filename}.pkl', 'wb') as f:
                pickle.dump(fresh_news_list, f)
            logger.error(f'Не удалось записать новости в final, файл {filename} сохранён для ручной обработки')


def check_and_move_to_asmi():
    """Валидирует с помощью модуля taste новости в таблице final и записывает валидное в antiSMI"""
    q = 'select * from final'
    final_news = DataBaseMixin.get(q, smi)
    if len(final_news):
        try:
            len_news = validate_and_write_to_asmi(final_news)
            logger.info(f'Успешно записано {len_news} новостей')
            erase_folder('pkl')
        except Exception as e:
            logger.exception(f'Не смог обработать из-за ошибки {e}')
