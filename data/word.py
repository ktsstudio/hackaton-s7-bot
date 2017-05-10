ALIASES = {
    'питер': 'санкт-петербург'
}


def aliaser(word):
    if word in ALIASES:
        return ALIASES[word]
    return word
