from imports.imports import logger, BlockingScheduler

from scripts.shop import go_shopping
from scripts.cook import cook_and_move_to_smi
from scripts.taste import check_and_move_to_asmi
from scripts.fix import gather_past_resume

'''
Orchestration module for antiSMI-Collector

Serves as an interface for managing 3 modules from scripts directory:
- shop.py: parses news from news agencies (like news "shopping")
- cook.py: generates titles and summaries for news collected by the shop.py module (like news "cooking")
- taste.py: validates "prepared" news for compliance with field types in databases and recording only correct data

There are two additional modules in the scripts folder:
- db.py: mandatory auxiliary module, contains a set of variables, classes and function for working with databases
- fix.py: optional auxiliary module, fixes problems with tomorrow article's resumes in the past (don't ask)

News from database is used by antiSMI-Bot (to create and send personal smart news digest via telegram interface) and 
by antiSMI-Monitor (to research social trends and to create NLP models)
'''


def shopping():
    """all_telegram_channel_news -> db.news"""
    go_shopping()


def cooking():
    """db.news -> db.final"""
    cook_and_move_to_smi()


def serving():
    """db.final -> db.antiSMI"""
    check_and_move_to_asmi()


def fixing():
    """adds daily resumes in past_machine.db if it was missing
    news with missing resume -> resume -> db.past_machine"""
    gather_past_resume()


if __name__ == '__main__':
    try:
        # This module serves for debugging the work of individual modules
        # serving()
        # shopping()
        # cooking()
        # serving()
        # fixing()

        scheduler = BlockingScheduler()
        scheduler.configure(timezone='Europe/Moscow')
        scheduler.add_job(fixing, 'cron', hour=0, minute=0, id='fixer',
                          max_instances=10, misfire_grace_time=600)
        scheduler.add_job(shopping, 'cron', hour='6-21, 23', minute=56, id='shopper',
                          max_instances=10, misfire_grace_time=600)
        scheduler.add_job(cooking, 'cron', hour='0, 7-21', id='cooker',
                          max_instances=10, misfire_grace_time=600)
        scheduler.add_job(serving, 'cron', hour='9-21/4, 23', minute=55, id='server',
                          max_instances=10, misfire_grace_time=600)
        scheduler.start()

    except Exception as e:
        logger.exception(e)
