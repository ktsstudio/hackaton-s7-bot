from instance import get_broker
from roboman.broker import stats
from tornado.ioloop import IOLoop
from settings import options
import logging

logger = logging.getLogger('broker')

if __name__ == '__main__':
    loop = IOLoop.instance()

    broker = get_broker()
    broker.listen(options.broker['port'], options.broker['host'])
    broker.set_telegram_webhook()

    loop.add_callback(stats)
    loop.start()
