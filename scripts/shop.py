from imports.imports import logger, random, dt, time, requests, re, BeautifulSoup, parser, EMOJI_DATA
from imports.phrase_dicts import black_labels

from scripts.db import DataBaseMixin, Query, smi, asmi
from scripts.taste import validate_and_write_to_news_db

'''This module is the Parser: it gathers news from news agencies by pre-cleaning them'''

logger.add('logs/debug_shop.json', format="{time} {message}", level='INFO', rotation="1 week",
           compression="zip",
           serialize=True)


class AgenciesID(DataBaseMixin):
    """
    Collects a dictionary of all existing news id's for each agency and works with it
    Собирает словарь всех существующих id новостей для каждого агентства и работает с ним
    """

    def __init__(self):
        self.ids_dict = dict()

    @staticmethod
    def __get_agencies_ids() -> dict:
        """
        Gives a dictionary of each agency's news id in the form {'agency': (id1, id2,...)}.
        Отдаёт словарь id-новостей каждого агентства в виде {'agency': (id1, id2,...)}
        """
        all_agencies_ids = {}
        news_ids = Query.get_all_ids(smi, 'news')
        final_ids = Query.get_all_ids(smi, 'final')
        error_ids = Query.get_all_ids(smi, 'error_table')
        asmi_ids = Query.get_all_ids(asmi, 'news')
        total_ids = [*news_ids, *final_ids, *error_ids, *asmi_ids]
        all_active_agencies_query = "SELECT telegram FROM agencies WHERE is_parsing is True"
        all_active_agencies = DataBaseMixin.get(all_active_agencies_query, asmi)

        for agency in all_active_agencies:
            articles_ids = tuple(
                el['id'] for el in total_ids if el['agency'] == agency['telegram'])
            all_agencies_ids[agency['telegram']] = articles_ids

        return all_agencies_ids

    @property
    def get_ids(self):
        """Getter to get id's dictionary"""
        return self.ids_dict if self.ids_dict else logger.error(f'Словарь id пока не сформирован')

    @property
    def set_ids(self):
        """Setter for collecting id's dictionary"""
        self.ids_dict = self.__get_agencies_ids() if not self.ids_dict else logger.error('Словарь id уже в наличие')

    @property
    def del_ids(self):
        """Deleter for cleaning id's dictionary"""
        self.ids_dict.clear()
        logger.info('Словарь id новостей успешно очищен')

    def get_agency(self, agency):
        """Allows you to get a dictionary of id's for the desired agency"""
        return self.ids_dict[agency]


class Parser(Query):
    """
    News gathering class: parses agency news, saves a news dictionary and allows to work with it
    Класс сбора новостей: парсит новости агентства, сохраняет словарь новостей и позволяет работать с ним
    """

    def __init__(self, channel: str, ids: tuple):
        self.channel = channel
        self.ids = ids
        self.news = []

    def __len__(self) -> int:
        return len(self.news)

    def __grab_news(self) -> list[dict]:
        """
        Grab the latest media news, cleans it up, creates a news dictionary and returns it
        Создаёт словарь последних новостей СМИ и возвращает его
        """
        my_news: list[dict] = []
        agency = self.channel
        agency_url = 'https://t.me/s/' + agency
        user_agents = open('proxy/user-agents.txt').read().splitlines()
        random_user_agent = random.choice(user_agents)
        headers = {'User-Agent': random_user_agent}
        answer = requests.get(agency_url, headers=headers)
        if answer and answer.status_code != 204:
            try:
                soup = BeautifulSoup(answer.text, features="html.parser")
                page = soup.body.main.section.find_all(attrs={'class': 'tgme_widget_message_bubble'})
                for news_content in page:
                    dirty_news = news_content.find(attrs={'class': 'tgme_widget_message_text js-message_text'})
                    news_id = int(news_content.find(attrs={'class': 'tgme_widget_message_date'}).get('href').split('/')[
                                      -1])
                    if dirty_news and (news_id not in self.ids):
                        url = news_content.find(attrs={'class': 'tgme_widget_message_date'}).get('href')
                        regex_url_tme = re.compile('https://t.me/[-_a-z]*$')
                        regex_url_http = re.compile("(https|http)://[-_a-zA-Z]*.[a-zA-Z]*[^/]$")
                        tag_a = dirty_news.find('a')
                        links = tag_a.get('href').split('?utm')[0] \
                            if not (not tag_a or not (not
                                                      tag_a.get('href').startswith((
                                                          'tg://resolve?domain=',
                                                          'https://t.me/+'))
                                                      and not regex_url_tme.search(tag_a.get('href'))
                                                      and not regex_url_http.search(tag_a.get('href'))
                                                      )) \
                            else url
                        links = links.split('?')[0] if not links.startswith('https://www.youtube.com/watch') else links
                        date = parser.parse(news_content.find(attrs={'class': 'time'}).get('datetime'))
                        news = dirty_news.text

                        # Bold text in a telegram often denotes a headline that needs special treatment
                        # Жирный текст в телеграмме часто обозначает заголовок, который требует особой обработки
                        if dirty_news.b:
                            title = dirty_news.find_all('b')
                            title = [word.text for word in title]
                            title = ' '.join(title)
                            try:
                                news = news.replace(title, title.rstrip('.') + '. ') \
                                    if title and title.split()[0].istitle() else news
                            except IndexError:
                                pass
                        news = Parser.clean_news(news, agency)
                        my_news.append({'url': url, 'date': date, 'news': news, 'links': links, 'agency': agency})
            except (ValueError, KeyError, AttributeError):
                print(f'Обработка {agency} не удалась')

        return my_news

    @property
    def get_news(self):
        return self.news

    @property
    def set_news(self):
        self.news = self.__grab_news() if not self.news else print('Новости уже собраны')

    @property
    def del_news(self):
        """Очищает словарь новостей"""
        self.news.clear()
        return 'Обработка источника завершена, новости удалены'

    @staticmethod
    def clean_news(news: str, channel: str) -> str:
        """
        Cleans the agency news from garbage according to the settings of the black_labels dictionary
        Очищает новость от мусора согласно настройкам словаря black_labels
        """
        total_label = {*black_labels[channel], *black_labels['common_labels']} if channel in black_labels.keys() \
            else {*black_labels['common_labels']}
        for label in total_label:
            news = news.replace(label, ' ')
        news = news.strip(u"\uFE0F").lstrip('. ').lstrip('.')
        news = ''.join(char for char in news if char not in EMOJI_DATA)
        news = news.replace("\xa0", ' ')
        news = news.replace('​​', ' ').replace("‍", ' ').replace(" ", ' ')
        news = news.replace('\n', ' ').replace('\t', ' ')
        news = re.sub("https?://[-/_.a-zA-Z0-9]*.[-/_.a-zA-Z]*/[-/_.a-zA-Z0-9]*$", " ", news)
        news = re.sub("(go.vc.ru|vc.ru)/[-/_.a-zA-Z0-9]*", " ", news)
        news = news.lstrip('. ').lstrip('.')
        news = re.sub(" +", " ", news).strip()
        return news


def go_shopping():
    """Основная функция сбора: собираем новости, валидируем поля на соответствие, пишем во временную базу news"""
    total_news = 0
    start_time = dt.datetime.now()
    logger.info(f'Начинается сбор новостей от {start_time}:')

    agencies_ids = AgenciesID()
    agencies_ids.set_ids
    for channel, ids_tuple in agencies_ids.get_ids.items():
        channel = Parser(channel, ids_tuple)
        channel.set_news
        if len(channel):
            len_news = validate_and_write_to_news_db(channel.get_news)
            logger.info(f'{channel.channel}: собрано {len_news} новостей')
            total_news += len_news
            channel.del_news
            time.sleep(random.randint(1, 3))
    agencies_ids.del_ids

    result_time = dt.datetime.now() - start_time
    logger.info(
        f'\nСбор завершен успешно. Скорость: {round(result_time.seconds / total_news, 2)}  новостей в секунду'
        f'\nПолучено {total_news} новостей за {round(result_time.seconds / 60, 2)} минут.\n')
