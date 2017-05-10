from datetime import datetime, timedelta

from dateutil.parser import parse
from tornkts.utils import to_int

from data import CITIES
from data.word import aliaser
from tools.utils import month_number
import re
import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def tokenize(text, **kwargs):
    text = re.sub(r'[^a-zA-Za-яA-ЯЁёЙй0-9\-.]+', ' ', text)
    text = list(filter(str, text.split(' ')))

    for i in range(len(text)):
        try:
            text[i] = text[i].lower()
            if not kwargs.get('disable_normal', False):
                text[i] = morph.parse(text[i])[0].normal_form
            text[i] = aliaser(text[i])
        except:
            pass

    return text


def search(text):
    src = None
    dst = None

    raw_date = []
    now_auto = False
    date = None

    text = tokenize(text)

    for word in text:
        try:
            city = re.sub(r'[^a-zA-Za-яA-ЯЁёЙй0-9\-]+', '', word)

            if city in CITIES:
                if src is None:
                    src = city
                elif dst is None:
                    dst = city

            temp_date = word_to_date(word)
            if isinstance(temp_date, datetime):
                date = temp_date
            elif temp_date:
                raw_date.append(temp_date)
        except:
            pass

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
                date = parse('.'.join(map(str, raw_date[0:3])))
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
    }


def word_to_date(word):
    if re.match(r'[0-9]{2,4}-[0-9]{2}-[0-9]{2}', word):
        return parse(word)
    if re.match(r'[0-9]{2}.[0-9]{2}.[0-9]{2,4}', word):
        return parse(word)

    if word == 'послезавтра':
        return datetime.now() + timedelta(days=2)

    if word == 'завтра':
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
