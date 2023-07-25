from dateutil.relativedelta import relativedelta
from db import *
from cook import article2resume

DB_USER = 'maxlethal_db'

time_machine = create_engine(
	f'postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_USER}', pool_pre_ping=True)


def gather_past_news():
	# now_date = dt.datetime.now().date()
	# years = [(now_date.year - year) for year in range(1999, now_date.year)]
	# years = [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23]
	# past_dates = tuple(now_date - relativedelta(years=year) for year in years)
	# in_str = ", ".join(f"'{date}'" for date in (past_dates))
	#
	# logger.info('Забираю новости из прошлого на обработку')
	# q = f"SELECT * FROM news WHERE date::date IN ({in_str}) AND resume IS NULL"
	# date_news = DataBaseMixin.get(q, time_machine)

	start_date = dt.datetime(year=2023, day=1, month=7).date()
	dates = [start_date + dt.timedelta(days=el) for el in range(20)]
	# years = [7,8,9,12,13,14,17,18,19]

	result_dates = []
	for date in dates:
		past_dates = tuple(date - relativedelta(years=year) for year in range(1, 26))
		result_dates.extend(past_dates)
	in_str = ", ".join(f"'{date}'" for date in (result_dates))

	q = f"SELECT * FROM news WHERE date::date IN ({in_str}) AND resume IS NULL"
	date_news = DataBaseMixin.get(q, time_machine)


	logger.info('Начинаю сбор недостающих резюме:')
	for i, news in enumerate(date_news[:1000]):
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
