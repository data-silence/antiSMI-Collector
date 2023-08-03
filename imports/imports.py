# Date and time libs:
import datetime as dt
import time
import pytz
from dateutil.relativedelta import relativedelta
from dateutil import parser

# File and folders libs:
import os
from pathlib import Path
from shutil import rmtree
import pickle

# Parsing libs:
import requests
from bs4 import BeautifulSoup
import re
from emoji import EMOJI_DATA

# Databases libs:
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, insert, MetaData, Table, Column, Text, TIMESTAMP
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum
# from typing import Optional

# Other libs:
import random
from loguru import logger
from apscheduler.schedulers.background import BlockingScheduler

# Language models:
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, T5ForConditionalGeneration
import fasttext as fasttext
import warnings

warnings.filterwarnings("ignore")
fasttext.FastText.eprint = lambda x: None
model_class = fasttext.load_model("models/cat_model.ftz")

tokenizer_resume = AutoTokenizer.from_pretrained("IlyaGusev/mbart_ru_sum_gazeta")
model_resume = AutoModelForSeq2SeqLM.from_pretrained("IlyaGusev/mbart_ru_sum_gazeta")

tokenizer_title = AutoTokenizer.from_pretrained("IlyaGusev/rut5_base_headline_gen_telegram")
model_title = T5ForConditionalGeneration.from_pretrained("IlyaGusev/rut5_base_headline_gen_telegram")
