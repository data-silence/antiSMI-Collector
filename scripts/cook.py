from imports.imports import logger, dt, pickle, Path, rmtree
from imports.imports import model_resume, tokenizer_title, tokenizer_resume, model_title, model_class

from scripts.db import DataBaseMixin, Query, smi

'''
This module generates new's headlines and annotations using summarization models and write full news items into db
Модуль генерирует заголовки и аннотации с использованием моделей суммаризации и записывает полный текст новости в базу
'''

logger.add('logs/debug_cook.json', format="{time} {message}", level='INFO', rotation="1 week", compression="zip",
           serialize=True)


def article2resume(article_text: str) -> str:
    """
    Creates news summaries using the mbart model
    Создаёт резюме новости с помощью модели mbart
    """
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
    """
    Creates a headline from a news summary using the ruT5 model
    Создаёт заголовок из резюме новости с помощью модели ruT5
    """
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
    """
    Main function of the module | Основная функция модуля

    Takes the agency's fresh news, makes a summary and headline for it, forms a dictionary to be recorded
    into the smi auxiliary database

    Забирает свежие новости агентства, делает к ним резюме и заголовок, формирует словарь свежих новостей для записи
    во вспомогательную базу данных smi
    """

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
            # process only news that are not assigned to the categories not_news and other
            # обрабатываем только новости, которым не присвоены категории not_news и other
            news['title'] = article2title(news['news'])
            news['resume'] = article2resume(news['news'])
            duration = (dt.datetime.now() - start_time).seconds
            logger_dict = {'duration': duration, 'url': news["url"]}
            logger.info(logger_dict)

    fixed_news = [news for news in fresh_news_list if news['category'] != 'other' and news['category'] != 'not_news']
    result_time = dt.datetime.now() - start_t

    logger.info('\nУспешно выполнено с результатами:')
    logger.info(f'Обработано: {len(fixed_news)} новостей')
    logger.info(f'Затрачено времени: {round(result_time.seconds / 60, 2)} минут')
    logger.info(f'Время обработки одной новости: {round(result_time.seconds / (len(fixed_news) + 0.01), 2)} секунд')
    logger.error(f'{len(fresh_news_list) - len(fixed_news)} отнесены к неновостным сообщениям и не обрабатывались')

    return fixed_news


def erase_folder(folder_name: str):
    """
    Clears all files in the specified folder
    Очищает все файлы в заданной папке
    """
    for path in Path(folder_name).glob('*'):
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()


def cook_and_move_to_smi():
    """
    Orchestration function of the module | Координирующая функция модуля

    Generates summary and headline for fresh news, writes them into final database for final validation
    Генерирует резюме и заголовок к свежим новостям, записывает их в базу final для проведения финальной валидации
    """
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
            logger.error(f'Не удалось записать новости в final, файл {filename} сохранён для ручной обработки\n')
