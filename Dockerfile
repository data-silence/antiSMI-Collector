FROM python:3.11

WORKDIR /app

COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY . /app
COPY proxy/ /app/proxy/
COPY debugging/ /app/debugging/
COPY pkl/ /app/pkl/


LABEL authors="maxlethal"
LABEL app_name='collector'

ENTRYPOINT ["python3", "main.py"]
