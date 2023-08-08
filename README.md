# antiSMI-Collector

The Collector is one of three parts of the [AntiSMI Project](https://maxlethal.notion.site/antiSMI-project-763ed7401b9f4e2cbee7cdf6f03ad0b9).

It is a parser of "fresh" news from news agencies into database for further use within the Project by other's parts:
* [Bot](https://t.me/antiSMI_bot) - to create and send personal smart news digest via telegram interface 
* **Monitor** - to research social trends, make dashboards and to create NLP models

![AntiSMI structure](https://github.com/maxlethal/antiSMI-Collector/blob/master/img/AntiSMI%20structure%20small.png)

### Collector's structure:

**main.py** serves as an interface for managing 3 modules from _scripts_ directory:
- **shop.py**: parses news from news agencies (similar to news "shopping")
- **cook.py**: generates titles and summaries for news collected by the shop.py module (similar to news "cooking")
- **taste.py**: validates "prepared" news for compliance with field types in databases and recording only correct data

There are two additional modules in the scripts folder:
- **db.py**: mandatory auxiliary module, contains a set of variables, classes and function for working with databases
- **fix.py**: optional auxiliary module, fixes problems with tomorrow article's resumes in the past (don't ask)
