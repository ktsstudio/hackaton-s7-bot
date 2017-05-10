import re
from datetime import datetime

from dateutil.relativedelta import relativedelta
from tornkts.utils import to_int

MONTH_TITLES = {
    '1': 'январь', '2': 'февраль',
    '3': 'март', '4': 'апрель', '5': 'май',
    '6': 'июнь', '7': 'июль', '8': 'август',
    '9': 'сентябрь', '10': 'октябрь', '11': 'ноябрь',
    '12': 'декабрь',
}

MONTH_TITLES_GENITIVE = {
    '1': 'января', '2': 'февраля',
    '3': 'марта', '4': 'апреля', '5': 'мая',
    '6': 'июня', '7': 'июля', '8': 'августа',
    '9': 'сентября', '10': 'октября', '11': 'ноября',
    '12': 'декабря',
}


def month_titles(genitive=False):
    result = MONTH_TITLES.values()
    if genitive:
        result += MONTH_TITLES_GENITIVE.values()
    return result


def month_number(name):
    months = dict()
    months.update(dict((v, k) for k, v in MONTH_TITLES.items()))
    months.update(dict((v, k) for k, v in MONTH_TITLES_GENITIVE.items()))

    return to_int(months.get(name))


def month_title(num, genitive=False):
    titles = MONTH_TITLES

    if genitive:
        titles = MONTH_TITLES_GENITIVE

    return titles.get(str(to_int(num)))


def readable_date(date):
    now = datetime.now()
    if now.year == date.year:
        return '{0} {1}'.format(date.day, month_title(date.month, True))
    else:
        return date.strftime('%d.%m.%Y')


def add_eleven_month(date=None):
    if date is None:
        date = datetime.now().date()
    return date + relativedelta(months=11)