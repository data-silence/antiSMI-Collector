from dateutil.relativedelta import relativedelta
import pytz
from db import *
from cook import article2resume


def gather_past_news():
    now_date = dt.datetime.now(pytz.timezone('Europe/Moscow')) + dt.timedelta(days=1)
    years = [(now_date.year - year) for year in range(1999, now_date.year)]
    past_dates = tuple(now_date - relativedelta(years=year) for year in years)
    in_str = ", ".join(f"'{date}'" for date in past_dates)

    logger.info(f'Забираю новости за {now_date.month} - {now_date.day} на обработку')
    q = f"SELECT * FROM news WHERE date::date IN ({in_str}) AND resume IS NULL"
    date_news = DataBaseMixin.get(q, time_machine)

    logger.info('Начинаю сбор недостающих резюме:')
    for i, news in enumerate(reversed(date_news)):
        logger.info(f"{i + 1}/{len(date_news)} {news['url']} - записываю")
        try:
            resume = article2resume(news['news'])
            resume = resume.replace("'", "`").strip()
            with time_machine.begin() as conn:
                q = f"""UPDATE news SET resume='{resume}' WHERE url='{news['url']}'"""
                conn.execute(text(q))
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    gather_past_news()
