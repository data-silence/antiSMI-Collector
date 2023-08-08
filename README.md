# antiSMI-Collector

The AntiSMI-Collector is one of three parts of the [AntiSMI Project](https://maxlethal.notion.site/antiSMI-project-763ed7401b9f4e2cbee7cdf6f03ad0b9).

It is a parser of breaking news from news agencies into database for further use within the Project.

News from database is used by antiSMI-Bot (to create and send personal smart news digest via telegram interface) and 
by antiSMI-Monitor (to research social trends and to create NLP models)

![AntiSMI structure](https://github.com/maxlethal/antiSMI-Collector/blob/master/img/AntiSMI%20structure.png)


Main.py serves as an interface for managing 3 modules from scripts directory:
- shop.py: parses news from news agencies (like news "shopping")
- cook.py: generates titles and summaries for news collected by the shop.py module (like news "cooking")
- taste.py: validates "prepared" news for compliance with field types in databases and recording only correct data

There are two additional modules in the scripts folder:
- db.py: mandatory auxiliary module, contains a set of variables, classes and function for working with databases
- fix.py: optional auxiliary module, fixes problems with tomorrow article's resumes in the past (don't ask)
