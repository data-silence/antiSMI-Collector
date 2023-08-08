from imports.imports import dt, logger, pytz, relativedelta

from scripts.db import DataBaseMixin, time_machine, text
from scripts.cook import article2resume


def gather_past_resume():
    """
    news without resume -> resume -> db.timemachine

    Optional auxiliary module | Вспомогательный необязательный модуль:

    Searches for all news in the last twenty years that don't have summaries, generates them and writes to db
    Ищет все новости за последние двадцать лет, которые не имеют резюме, генерирует их и пишет в базу
    """

    # We want to get all missing summaries for tomorrow date for all time periods in the past.
    # So our starting date is tomorrow.
    start_date = dt.datetime.now(pytz.timezone('Europe/Moscow')) + dt.timedelta(days=1)
    years = [(start_date.year - year) for year in range(1999, start_date.year)]
    past_dates = tuple(start_date - relativedelta(years=year) for year in years)
    in_str = ", ".join(f"'{date}'" for date in past_dates)

    # Selecting news without summaries
    logger.info(f'Starting to process missing resumes for {start_date.month} - {start_date.day}')
    q = f"SELECT * FROM news WHERE date::date IN ({in_str}) AND (resume IS NULL OR resume = '')"
    date_news = DataBaseMixin.get(q, time_machine)

    for i, news in enumerate(reversed(date_news)):
        logger.info(f"{i + 1}/{len(date_news)} {news['url']} - записываю")
        try:
            # send news to summarization model
            resume = article2resume(news['news'])
            # to avoid the error of writing to the database news containing an apostrophe
            resume = resume.replace("'", "`").strip()
            with time_machine.begin() as conn:
                q = f"""UPDATE news SET resume='{resume}' WHERE url='{news['url']}'"""
                conn.execute(text(q))
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    gather_past_resume()
