from shop import *
from cook import *
from pytz import utc
from past_resume_fixer import *
from apscheduler.schedulers.background import BlockingScheduler


def shopping():
    """agency telegram channel -> temp.db, table.news"""
    go_shopping()


def cooking():
    """temp.db, table.news -> temp.db, table.final"""
    cook_and_move_to_smi()


def serving():
    """temp.db, table.final -> antiSMI"""
    check_and_move_to_asmi()

def fixing():
    """add daily resumes in past_machine.db if it was missing"""
    gather_past_news()

if __name__ == '__main__':
    try:
        # shopping()
        # cooking()
        # serving()
        # fixing()
        scheduler = BlockingScheduler()
        scheduler.configure(timezone='Europe/Moscow')
        scheduler.add_job(fixing, 'cron', hour=0, id='fixer', max_instances=10, misfire_grace_time=600)
        scheduler.add_job(shopping, 'cron', hour='6-22', minute=55, id='shopper', max_instances=10, misfire_grace_time=600)
        scheduler.add_job(cooking, 'cron', hour='7-23', id='cooker', max_instances=10, misfire_grace_time=600)
        scheduler.add_job(serving, 'cron', hour='9-21/4', minute=50, id='server', max_instances=10,
                          misfire_grace_time=600)


        scheduler.start()


    except Exception as e:
        logger.exception(e)
