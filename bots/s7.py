from datetime import datetime
from dateutil.parser import parse

from bots.subbot.buy import BuyBot
from roboman.bot.bot import BaseBot
from tornkts.utils import to_int
from roboman.exceptions import BotException
from tools import extractor
from tools.extractor import flight_cost
from tools.utils import readable_date, add_eleven_month


class S7Bot(BaseBot):
    @property
    def state(self):
        if self.user:
            return self.user.get('state')
        return None

    def set_state(self, state):
        if not self.user:
            self.user = dict()
        self.user['state'] = state

    async def before_hook(self):
        self.user = await self.store.db.users.find_one({'external': self.msg.unique_key})

        if self.user is None:
            self.user = {
                'external': self.msg.unique_key,
                'last_use': to_int(datetime.now().timestamp()),
                'state': self.state
            }

    async def after_hook(self):
        await self.store.db.users.update_one(
            {'external': self.msg.unique_key},
            {'$set': self.user},
            upsert=True,
        )

    async def hook(self):
        if not self.state:
            flight = await self.buy_detector()
            if flight:
                self.user['flight'] = flight
                self.set_state('buy')

        if self.state == 'buy':
            await self.run(BuyBot)
        else:
            is_common_phrases = await self.common_phrase()
            await self.search(is_common_phrases)

    async def search(self, is_common_phrases):
        extract = extractor.search(self.msg.text)

        src = extract['src']
        dst = extract['dst']
        date = extract['date']

        if datetime.now().date() > date.date():
            raise BotException('В расписании отображаются только будущие рейсы')

        if add_eleven_month() < date.date():
            raise BotException('Расписание составлено только на 11 месяцев вперед от текущей даты')

        if date is not None and not extract['now_auto'] and (src is None and dst is None):
            if 'last_rasp_request' in self.user:
                src = self.user['last_rasp_request'].get('src')
                dst = self.user['last_rasp_request'].get('dst')

        if src and dst and date:
            rasp_params = dict(
                src=src, dst=dst,
                date=date.strftime('%Y-%m-%d'),
                extra=dict(transport_types='plane')
            )
            self.user['last_rasp_request'] = rasp_params
            rasp = await self.store.yandex_rasp.fetch(**rasp_params)

            results = dict()
            for item in rasp.get('threads'):
                try:
                    departure = parse(item['departure'])
                    arrival = parse(item['arrival'])
                    if departure < datetime.now():
                        continue

                    attrs = {
                        'departure': departure,
                        'arrival': arrival,
                        'id': item['thread']['number'].replace(' ', ''),
                        'from': item['from']['title'],
                        'to': item['to']['title']
                    }

                    route = '\n{0} — {1}'.format(attrs['from'], attrs['to'])

                    if route not in results:
                        results[route] = []

                    results[route].append(attrs)
                except KeyError:
                    pass

            if len(results) > 0:
                response = 'Рейсы на {0}\n'.format(readable_date(date))
                for route, items in results.items():
                    response = response + '{0}:\n'.format(route)
                    for item in items:
                        cost = flight_cost(item)

                        response += '{id} в {departure} за {cost} ₽\n'.format(
                            id=item['id'],
                            departure=item['departure'].strftime('%H:%M'),
                            cost=cost,
                        )

                response += '\nДля заказа билета введите номер рейса'
                await self.send(response.strip())
            else:
                await self.send('Не нашлось рейсов на {0}'.format(readable_date(date)))
        else:
            msg = ''
            if not (is_common_phrases and src is None and dst is None):
                msg = 'Мы не поняли {direction} нужно лететь. '
            await self.send(
                (msg + 'Напишите в свободной форме о вашем путешествии').format(
                    direction='откуда' if src is None else 'куда'
                )
            )

    async def buy_detector(self):
        text = set(extractor.tokenize(self.msg.text))

        if 'last_rasp_request' in self.user:
            last_rasp_request = self.user['last_rasp_request']
            rasp = await self.store.yandex_rasp.fetch(**last_rasp_request)
            for item in rasp.get('threads'):
                number = item['thread']['number'].replace(' ', '').lower()

                if number in text:
                    return item

        return False

    async def common_phrase(self):
        text = set(extractor.tokenize(self.msg.text))

        to_response = set()
        detect = {
            'greetings': ['привет', 'приветик', 'хай', 'здравствуйте', 'здравствуй', 'здарова', 'hi', 'hello', 'bonjour']
        }
        responses = {
            'greetings': 'Hello',
        }

        for key, keywords in detect.items():
            for keyword in keywords:
                if keyword in text:
                    to_response.add(key)
                    break

        for item in to_response:
            message = responses.get(item)
            if not message:
                continue

            if item == 'greetings':
                now = datetime.now()
                if 0 <= now.hour < 4:
                    message = 'Доброй ночи!'
                elif 4 <= now.hour < 12:
                    message = 'Доброе утро'
                elif 12 <= now.hour < 18:
                    message = 'Добрый день'
                else:
                    message = 'Добрый вечер'

            await self.send(message)

        return len(to_response) > 0
