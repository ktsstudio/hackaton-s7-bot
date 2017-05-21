from datetime import datetime, timedelta

from bson import ObjectId
from dateutil.parser import parse
from tornado import gen
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.httputil import url_concat
from tornado.ioloop import IOLoop
from tornkts.utils import json_loads

from instance import get_worker
from roboman.bot.message import Message

client = AsyncHTTPClient()


@gen.coroutine
def notifications():
    worker = get_worker()

    def create_bot(user):
        source, from_id = user.get('external', '').split(':')

        msg = Message(source=source, from_id=from_id)
        return worker.bot_instance(msg)

    while True:
        cursor = worker.store.db.reserving.find()
        while (yield cursor.fetch_next):
            try:
                ticket = cursor.next_object()
                if ticket.get('weather'):
                    continue

                departure = parse(ticket['flight']['departure'])
                now = datetime.now()
                now -= timedelta(hours=24)
                print(departure, now)
                if departure > now:
                    to = ticket['flight']['to']['title']

                    req = HTTPRequest(
                        url=url_concat(
                            'http://api.openweathermap.org/data/2.5/weather',
                            {
                                'APPID': '4c9bb6c2fb1800b3d01343f22867d2cc',
                                'q': to,
                                'units': 'metric',
                            }
                        )
                    )

                    res = yield client.fetch(req)
                    res = json_loads(res.body)

                    user = yield worker.store.db.users.find_one({'_id': ObjectId(ticket.get('user_id'))})

                    if user and res:
                        bot = create_bot(user)

                        temp = res['main']['temp']

                        if temp < 15:
                            advice = 'одевайтесь теплее!'
                        elif 15 < temp < 25:
                            advice = 'температура комфортная'
                        else:
                            advice = 'аккуратнее на жаре!'

                        yield bot.send('По прибытии в {to} ожидается температура {temp}° С, {advice}'.format(
                            to=to,
                            temp=round(temp),
                            advice=advice
                        ))

                        ticket['weather'] = 1

                        _id = ticket.get('_id')
                        if '_id' in ticket:
                            del ticket['_id']

                        yield worker.store.db.reserving.update_one(
                            {'_id': ObjectId(_id)},
                            {'$set': ticket},
                            upsert=True
                        )
            except Exception as e:
                print(e)

        yield gen.sleep(60)


if __name__ == '__main__':
    loop = IOLoop.instance()
    loop.add_callback(notifications)
    loop.start()
