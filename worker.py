from tornado.ioloop import IOLoop
from instance import get_worker
from tools.extractor import get_wv

if __name__ == '__main__':
    get_wv()

    loop = IOLoop.instance()
    worker = get_worker()
    loop.run_sync(worker.store.search.connect)
    worker.start(loop=loop)
    loop.run_sync(worker.store.search.disconnect)

    loop.start()
