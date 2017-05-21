import re

ALIASES = {
    'питер': 'санкт-петербург',
    'спб': 'санкт-петербург',
    'мск': 'москва',
    'екб': 'екатеринбург',
    'новосиб': 'новосибирск',
    'нск': 'новосибирск',
}


def aliaser(word):
    temp = re.sub(r'[^a-zA-Za-яA-ЯЁёЙй0-9\-]+', '', word)
    if temp in ALIASES:
        return ALIASES[temp]
    return word
