from tornado.ioloop import IOLoop
from roboman.worker import Worker
from bots.s7 import S7Bot
from settings import options

if __name__ == '__main__':
    loop = IOLoop.instance()

    worker = Worker(bot=S7Bot, **options.worker)
    worker.start(loop=loop)

    loop.start()
