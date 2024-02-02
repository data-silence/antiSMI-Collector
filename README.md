# antiSMI-Collector
![Parser stats](https://github.com/maxlethal/antiSMI-Collector/blob/master/img/Parser%20stats.png?raw=true)

![Apache Superset](https://img.shields.io/badge/Superset-black?style=flat-square&logo=Superset) ![Pydantic](https://img.shields.io/badge/Pydantic-black?style=flat-square&logo=Pydantic) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-black?style=flat-square&logo=PostgreSQL) ![SQLalchemy](https://img.shields.io/badge/SQLalchemy-black?style=flat-square&logo=sqlalchemy) ![Docker](https://img.shields.io/badge/Docker-black?style=flat-square&logo=Docker) ![BS4](https://img.shields.io/badge/BeautifulSoup4-black?style=flat-square&logo=BS4) ![Requests](https://img.shields.io/badge/Requests-black?style=flat-square&logo=Requests) 

## Table of contents

* [About](#about)
* [Stats](#stats)
* [Stack](#stack)
* [ML models](#ml-models)
* [Development Tools](#development-tools)
* [Code's structure](#code-structure)


## About

The Collector is one of three parts of the [AntiSMI Project](https://github.com/maxlethal/antiSMI-Project).

It is designed to constantly collect fresh news from various sources, process and store them for further use within the Project by other's parts:
* [Bot](https://github.com/maxlethal/antiSMI-Bot) - to create and send personal smart news digest via telegram interface 
* **Observer** - to research social trends, make dashboards and to create NLP models

In news processing, trained machine learning models are used to categorize the news and create its summary and title.

## Stats
* **Start:** 2022-07-01 [project suspended for 2 months in 2022]
* **Capacity:** 40 news agencies, 500 news/day
* **Bot database capacity:** > 100,000 news articles [07.2022 - today]
* **Archive base capacity:** > 1.5 million articles [08.1999 - 04.2019]

## Stack

* **Language:** python, sql 
* **Databases:** postgreSQL, sqlalchemy
* **Validation:** pydantic
* **Logging:** loguru
* **BI**: apache SuperSet
* **Scraping:**  requests, Beatufill Soup 4

## ML models:

- **Summarization:**
    - mBart, Seq2Seq, pre-trained [news summary]
    - ruT5, pre-trained [headline]
- **Categorization:**
    - fasttext, supervised pre-training, 7 classes (categories)

**Clustering** problems are solved by [AntiSMI-Bot](https://github.com/maxlethal/antiSMI-Bot).

## Development Tools:
- Pycharm
- Docker
- GitHub
- Linux shell


## Code structure:

**main.py** serves as an interface for managing 3 modules from _scripts_ directory:
- **shop.py**: parses news from news agencies (similar to news "shopping")
- **cook.py**: generates titles and summaries for news collected by the shop.py module (similar to news "cooking")
- **taste.py**: validates "prepared" news for compliance with field types in databases and recording only correct data

There are two additional modules in the scripts folder:
- **db.py**: mandatory auxiliary module, contains a set of variables, classes and function for working with databases
- **fix.py**: optional auxiliary module, fixes problems with article's resumes in the Bot's "past machine" module

