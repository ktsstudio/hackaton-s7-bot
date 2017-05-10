from roboman.broker import Broker, stats
from tornado.ioloop import IOLoop
from settings import options
import logging

logger = logging.getLogger('broker')

if __name__ == '__main__':
    loop = IOLoop.instance()

    settings = {
        'debug': options.debug,
        'messengers': options.messengers,
        'access_token': options.broker.get('access_token'),
    }

    broker = Broker(settings=settings)
    broker.listen(options.broker['port'], options.broker['host'])
    broker.set_telegram_webhook()

    loop.add_callback(stats)
    loop.start()
