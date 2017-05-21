import re
from os import path
import csv
from string import punctuation

import pandas as pd
import pymorphy2
from nltk.corpus import stopwords

CURRENT_DIR = path.dirname(path.abspath(__file__))
CITIES = set()

with open(path.join(CURRENT_DIR, 'regions.csv'), 'r', encoding='UTF-8') as csvfile:
    rows = list(csv.reader(csvfile, delimiter=';', quotechar='|'))

    for row in rows:
        city = str(row[3]).strip().lower()
        if city:
            CITIES.add(city)

morph = pymorphy2.MorphAnalyzer()

STOP = set(stopwords.words('russian')) | set([str(i) for i in range(9)])
stops = set(stopwords.words('russian'))


def to_normal_form(words):
    normals = []
    for w in words:
        w = re.sub(r'\W+', '', w)
        if w:
            w = morph.parse(w)[0].normal_form
            normals.append(w)
    return normals


def singular_words(sentence):
    s = ''.join([c for c in sentence if c not in punctuation])
    s = s.lower().split()
    with_stop = [w for w in s if w in STOP]
    without_stop = ' '.join([w for w in s if w not in STOP])
    words_without_stop = to_normal_form(without_stop)
    with_stop.extend(words_without_stop)
    return with_stop


def normalize(text):
    #     text = replaces(text)
    #     text = ''.join([c for c in text if c not in punctuation])
    #     text = ''.join([c for c in text if c not in punctuation])
    #     text = replaces(text)
    text = ''.join([c for c in text if c not in punctuation])
    words = text.lower().split()
    words = to_normal_form(words)
    #     words = [w for w in text if len(w) > 2]
    #     words = str(text).lower().split()
    return words


def prepare(row):
    return normalize(row)


# df = pd.read_csv(path.join(CURRENT_DIR, 'faq.csv'),
#                  names=['category', 'title', 'text'])
# FAQ_DF = df
# FAQ_RAW = df['title']
# FAQ = df['title'].apply(lambda x: prepare(x))
