from roboman.worker import Worker
from bots.s7 import S7Bot
from roboman.broker import Broker
from settings import options


def get_worker():
    settings = options.worker
    settings['messengers'] = options.messengers
    settings['stores'] = options.stores
    settings['bot'] = options.bot

    return Worker(bot_cls=S7Bot, **settings)


def get_broker():
    settings = {
        'debug': options.debug,
        'messengers': options.messengers,
        'access_token': options.broker.get('access_token'),
    }

    return Broker(settings=settings)
