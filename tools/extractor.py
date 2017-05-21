import os
import enum
import random
from datetime import datetime, timedelta

import editdistance
from dateutil.parser import parse
from tornkts.utils import to_int

from data import CITIES
from data.word import aliaser
from tools import wordvectors
from tools.loader import load_vectors
from tools.utils import month_number
import re
import pymorphy2
import numpy as np

morph = pymorphy2.MorphAnalyzer()

WV = None

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_wv():
    global WV
    if WV is None:
        WV = load_vectors(os.path.join(CURRENT_DIR, '..', './data/large/ruscorpora_russe.model.bin'))
        # WV = wordvectors.load('./ruscorpora_russe.model.bin', root_dir='./data/large')
    return WV
#
#
# get_wv()


def tokenize(text, disable_normal=False, return_tags=False):
    text = re.sub(r'[^a-zA-Za-яA-ЯЁёЙй0-9\-.]+', ' ', text)
    text = list(filter(str, text.split(' ')))

    tags = []

    for i in range(len(text)):
        try:
            text[i] = text[i].lower()
            m = morph.parse(text[i])[0]

            if not disable_normal:
                text[i] = m.normal_form
            text[i] = aliaser(text[i])

            tags.append(m.tag)
        except:
            pass

    if return_tags:
        return text, tags
    return text


def is_unknown_destination(text):
    return re.search(r'(куда[-\s]{0,3}нибудь)|(вс[её][-\s]{0,3}равно)', text) is not None


def get_suggestions_for_src(src):
    popular_destinations = ['Осака', 'Петропавловск-Камчатский', 'Сеул', 'Токио', 'Шанхай ', 'Бангкок', 'Сеул', 'Утапао', 'Аликанте', 'Анапа', 'Барселона ', 'Батуми ', 'Берлин', 'Бургас', 'Валенсия', 'Варна', 'Вена ', 'Верона', 'Генуя ', 'Горно-Алтайск', 'Дубровник', 'Ереван', 'Ибица', 'Калининград', 'Катания ', 'Кос ', 'Краснодар', 'Кутаиси ', 'Ларнака ', 'Мадрид', 'Малага', 'Минеральные Воды', 'Мюнхен', 'Неаполь', 'Пальма Мальорка', 'Пафос', 'Петрозаводск ', 'Пиза ', 'Пула', 'Родос', 'Симферополь', 'Сочи', 'Тбилиси', 'Тиват', 'Анапа', 'Бургас', 'Горно-Алтайск', 'Ереван', 'Краснодар', 'Минеральные Воды', 'Петропавловск-Камчатский', 'Сеул ', 'Симферополь', 'Сочи', 'Тбилиси', 'Шанхай', 'Берлин ', 'Калининград', 'Токио']
    return random.sample(popular_destinations, 5)


def search(text):
    src = None
    dst = None

    raw_date = []
    now_auto = False
    date = None

    from_preps = [
        'из'
    ]

    to_preps = [
        'в'
    ]

    text, tags = tokenize(text, return_tags=True)

    all_cities = set()

    cities = []

    previous_word = None
    for word in text:
        try:
            city = re.sub(r'[^a-zA-Za-яA-ЯЁёЙй0-9\-]+', '', word)
            print(city)
            if city in CITIES:
                cities.append(city)
                all_cities.add(city)

            temp_date = word_to_date(word, previous_word)
            if isinstance(temp_date, datetime):
                date = temp_date
            elif temp_date:
                raw_date.append(temp_date)

            previous_word = word
        except:
            pass

    def find_nearest_city_to_word(word_pos):
        if not (0 <= word_pos < len(text)):
            return None
        for i in range(word_pos, len(text)):
            w = text[i]

            if w in all_cities:
                return w

    changed_smartly = False
    for i, pair in enumerate(zip(text, tags)):
        w, tag = pair
        if 'PREP' in tag:
            nearest_city = find_nearest_city_to_word(i + 1)
            if nearest_city is not None:
                if w in from_preps:
                    src = nearest_city
                    changed_smartly = True
                elif w in to_preps:
                    dst = nearest_city
                    changed_smartly = True

    if not changed_smartly and len(cities) > 1:
        src, dst = cities[0], cities[1]

    if not date and len(raw_date) > 1:
        try:
            year_appended = False
            if len(raw_date) == 2:
                year_appended = True
                raw_date.append(datetime.now().year)

            date = parse('.'.join(map(str, raw_date[0:3])), dayfirst=True)

            if date < datetime.now() and year_appended:
                raw_date = raw_date[0:2]
                raw_date.append(datetime.now().year + 1)
                date = parse('.'.join(map(str, raw_date[0:3])), dayfirst=True)
        except:
            pass

    if not date:
        date = datetime.now()
        now_auto = True

    return {
        'src': src,
        'dst': dst,
        'date': date,
        'now_auto': now_auto,
        'cities': cities,
    }


def word_to_date(word, previous_word):
    if re.match(r'[0-9]{2,4}-[0-9]{2}-[0-9]{2}', word):
        return parse(word, dayfirst=True)
    if re.match(r'[0-9]{2}.[0-9]{2}.[0-9]{2,4}', word):
        return parse(word, dayfirst=True)

    if word == 'неделя':
        if previous_word == 'через':
            return datetime.now() + timedelta(days=7)

    if word == 'послезавтра':
        return datetime.now() + timedelta(days=2)

    if word == 'сегодня':
        return datetime.now()

    if word == 'завтра':
        if previous_word == 'после':
            return datetime.now() + timedelta(days=2)
        return datetime.now() + timedelta(days=1)

    temp = to_int(word)
    if temp:
        return temp

    temp = month_number(word)
    if temp:
        return temp

    return False


def cv(text):
    result = {}
    count = 0

    sn_pos = None
    n_pos = None
    pat_pos = None

    text = tokenize(text, disable_normal=True)
    sex_points = {
        'm': 0,
        'f': 0,
    }

    def update_sex_points(tag):
        if 'masc' in tag:
            sex_points['m'] += 1
        if 'femn' in tag:
            sex_points['f'] += 1

    def get_tag(word):
        return morph.tag(word)[0]

    for word in text:
        try:
            tag = get_tag(word)

            if len(word) == 10 and to_int(word, 0) > 0:
                result['passport'] = word

            if 'Surn' in tag:
                sn_pos = count
                result['surname'] = word.title()
                update_sex_points(tag)

            if 'Name' in tag:
                n_pos = count
                result['name'] = word.title()
                update_sex_points(tag)

            if 'Patr' in tag:
                pat_pos = count
                result['patronymic'] = word.title()
                update_sex_points(tag)

            try:
                birthday = parse(word, dayfirst=True)
                if isinstance(birthday, datetime):
                    result['birthday'] = birthday.strftime('%d.%m.%Y')
            except:
                pass

        except Exception as e:
            print(e)

        count += 1

    if n_pos is None and sn_pos is not None and pat_pos is not None:
        if sn_pos < pat_pos and pat_pos - sn_pos == 2 and sn_pos + 1 < len(text):
            n_pos = sn_pos + 1
        elif sn_pos > pat_pos and sn_pos - pat_pos == 1 and pat_pos > 0:
            n_pos = pat_pos - 1
        if n_pos is not None:
            result['name'] = text[pat_pos - 1].title()
            update_sex_points(get_tag(result['name']))

    if sn_pos is None and n_pos is not None and pat_pos is not None:
        if n_pos < pat_pos and pat_pos - n_pos == 1:
            sn_pos = n_pos - 1 if n_pos > 0 else pat_pos + 1
            result['surname'] = text[sn_pos].title()
            update_sex_points(get_tag(result['surname']))

    if sex_points['m'] != sex_points['f']:
        if sex_points['m'] > sex_points['f']:
            result['sex'] = 'm'
        else:
            result['sex'] = 'f'

    return result


def flight_cost(flight):
    departure = flight.get('departure')
    if not isinstance(departure, datetime):
        departure = parse(departure)

    arrival = flight.get('arrival')
    if not isinstance(arrival, datetime):
        arrival = parse(arrival)

    time = arrival - departure
    price_per_second = 0.508

    return to_int(price_per_second * time.seconds)


def similarity(w1, w2):
    w2v = get_wv()

    if w1 in w2v and w2 in w2v:
        return get_wv().similarity(w1, w2)

    editdist = editdistance.eval(w1, w2)
    max_len = max(len(w1), len(w2))
    return (max_len - editdist) / max_len


class QuestionType(enum.IntEnum):
    NONE = 0
    SEARCH = 1
    REGISTRATION = 2
    FAQ = 3


def detect_question(text, threshold=0.7):
    words = tokenize(text, disable_normal=False, return_tags=False)
    print(words)

    buy_tickets_kw = [
        'отправиться',
        'лететь',
        'билет'
    ]

    reg_kw = [
        'регистрация',
        'регистрироваться',
        'зарегистрироваться',
        'онлайн',
        'бронирование',
    ]

    faq_kw = [
        'как',
        'что',
        'сколько',
        'когда',
        'каким',
        'какой',
        'можно'
    ]

    pairs = [
        (QuestionType.SEARCH, buy_tickets_kw),
        (QuestionType.REGISTRATION, reg_kw),
        (QuestionType.FAQ, faq_kw),
    ]

    weights = {}
    for k in QuestionType:
        weights[k] = 0.0

    for w in words:
        for q_type, kw_arr in pairs:
            count = 0
            for kw in kw_arr:
                sim = similarity(w, kw)
                if sim > threshold:
                    weights[q_type] += sim
                    count += 1
            if count > 0:
                weights[q_type] /= count

    has_city = False
    is_date = False
    previous_word = None
    for word in words:
        city = re.sub(r'[^a-zA-Za-яA-ЯЁёЙй0-9\-]+', '', word)

        if city in CITIES:
            has_city = True

        if word_to_date(word, previous_word):
            is_date = True

        previous_word = word

    if has_city or is_date:
        return QuestionType.SEARCH

    max_type, max_value = None, 0
    for k, v in weights.items():
        if v > max_value:
            max_value = v
            max_type = k

    print('max_type: {}, max_weight: {}'.format(repr(max_type), max_value))
    if max_value == 0:
        return QuestionType.NONE
    else:
        if weights[QuestionType.FAQ] > 0.5:
            return QuestionType.FAQ
        return max_type
