# antiSMI-Collector

The Collector is one of three parts of the [AntiSMI Project](https://github.com/maxlethal/antiSMI-Project).

It is a parser of "fresh" news from news agencies into database for further use within the Project by other's parts:
* [Bot](https://github.com/maxlethal/antiSMI-Bot) - to create and send personal smart news digest via telegram interface 
* **Observer** - to research social trends, make dashboards and to create NLP models

## Stats
![Parser stats](https://github.com/maxlethal/antiSMI-Collector/blob/master/img/Parser%20stats.png?raw=true)


## Stack and Tools

* **Language:** python, sql 
* **Databases:** postgreSQL, sqlalchemy
* **Validation:** pydantic
* **Logging:** loguru
* **BI**: apache SuperSet

- **Scraping:**
    - requests
    - beatufill soup 4
- **Summarization:**
    - mBart, Seq2Seq, pre-trained [news summary]
    - ruT5, pre-trained [headline]
- **Categorization:**
    - fasttext, supervised pre-training, 7 classes (categories)

- **Development Tools:**
- Pycharm
- Docker
- GitHub
- Linux shell


## Code's structure:

**main.py** serves as an interface for managing 3 modules from _scripts_ directory:
- **shop.py**: parses news from news agencies (similar to news "shopping")
- **cook.py**: generates titles and summaries for news collected by the shop.py module (similar to news "cooking")
- **taste.py**: validates "prepared" news for compliance with field types in databases and recording only correct data

There are two additional modules in the scripts folder:
- **db.py**: mandatory auxiliary module, contains a set of variables, classes and function for working with databases
- **fix.py**: optional auxiliary module, fixes problems with article's resumes in the Bot's "past machine" module

