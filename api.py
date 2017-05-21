import weakref
from api.buy import BuyHandler
from bots.s7 import S7Bot
from instance import get_worker
from roboman.log import get_logger
from tornado.ioloop import IOLoop
from tornado.web import Application
from roboman.stores import StoreSet
from settings import options

logger = get_logger('broker')


class Api(Application):
    def __init__(self, *args, **kwargs):
        handlers = [
            (r"/buy.(.*)", BuyHandler),
        ]

        settings = {
            'compress_response': False,
            'debug': False,
            'worker': get_worker()
        }

        super().__init__(handlers, **settings)


if __name__ == '__main__':
    loop = IOLoop.instance()

    broker = Api()
    broker.listen(options.api['port'], options.api['host'])

    loop.start()
