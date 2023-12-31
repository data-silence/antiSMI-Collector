from imports.imports import logger, dt, pickle, Path, rmtree
from imports.imports import model_resume, tokenizer_title, tokenizer_resume, model_title, model_class

from scripts.db import DataBaseMixin, Query, russian

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
    into the auxiliary database russian

    Забирает свежие новости агентства, делает к ним резюме и заголовок, формирует словарь свежих новостей для записи
    во вспомогательную базу данных russian
    """

    if not DataBaseMixin.is_not_empty('news'):
        logger.error(
            f'News processing cannot start because the news has not yet been collected | '
            f'Обработка новостей не может начаться, так как новости ещё не собраны')
        logger.info('Collect news using the parse module | Соберите новости с помощью модуля parse')

    mono_dict = Query.get_monocategory_dict()
    all_fresh_news_query = "SELECT * FROM news"
    all_fresh_news_alchemy = DataBaseMixin.get(all_fresh_news_query, russian)
    fresh_news_list = [dict(fresh_news) for fresh_news in all_fresh_news_alchemy if 'url' in dict(fresh_news).keys()]

    start_time = dt.datetime.now()
    logger.info(f'News processing begins | Начинается обработка новостей -> {start_time}:')

    for i, news in enumerate(fresh_news_list):
        category = model_class.predict(news['news'])[0][0].split('__')[-1]
        if category not in ('other', 'not_news'):
            # process only news that are not assigned to the categories not_news and other
            # обрабатываем только новости, которым не присвоены категории not_news и other
            begin_time = dt.datetime.now()
            news['category'] = mono_dict[news['agency']] if news['agency'] in mono_dict.keys() else category
            news['title'] = article2title(news['news'])
            news['resume'] = article2resume(news['news'])
            duration = (dt.datetime.now() - begin_time).seconds
            logger_dict = {'position': f'{i + 1}/{len(fresh_news_list)}', 'duration': duration, 'url': news["url"]}
            logger.info(logger_dict)

    fixed_news = [news for news in fresh_news_list if 'category' in news]
    result_time = dt.datetime.now() - start_time

    logger.info('\nSuccessfully executed with the results | Успешно выполнено с результатами:')
    logger.info(f'Processed | Обработано: {len(fixed_news)} news')
    logger.info(f'Time taken | Затрачено времени: {round(result_time.seconds / 60, 2)} minutes')
    logger.info(f'Processing time of one news item | Время обработки новости: '
                f'{round(result_time.seconds / (len(fixed_news) + 0.01), 2)} sec')
    logger.error(f'Сategorized as non-news items and not processed | '
                 f'Отнесены к неновостным сообщениям, не обрабатывались: {len(fresh_news_list) - len(fixed_news)} news')

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
            logger.exception(f'Cause of error | Причины ошибки: {e}')
            filename = \
                str(dt.datetime.now()).split()[0] + '-' + str(dt.datetime.now()).split()[-1].split('.')[-1]
            with open(f'pkl/{filename}.pkl', 'wb') as f:
                pickle.dump(fresh_news_list, f)
            logger.error(f'Failed to record news in final, file saved for manual processing | '
                         f'Не удалось записать новости в final, файл сохранён для ручной обработки: -> {filename}\n')
