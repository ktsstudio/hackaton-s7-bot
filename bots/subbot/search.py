import random
from datetime import datetime
from dateutil.parser import parse
from roboman.exceptions import BotException
from roboman.bot.bot import BaseBot
from tools import extractor
from tools.extractor import morph, flight_cost
from tools.utils import add_eleven_month, readable_date


class SearchBot(BaseBot):
    @property
    def confirm_message(self):
        if self.is_telegram:
            return '/ok'
        if self.is_vk:
            return 'Да'

    @property
    def cancel_message(self):
        if self.is_telegram:
            return '/cancel'
        if self.is_vk:
            return 'Отмена'

    @property
    def user(self):
        return self.parent.user

    async def hook(self):
        if self.match_command(self.cancel_message):
            self.reset()
            await self.send('Вы отменили поиск')
            return

        await self.search(self.extra.get('is_common_phrases', False))

    async def search(self, is_common_phrases):
        extract = extractor.search(self.msg.text)
        print(extract)

        src = extract['src']
        dst = extract['dst']
        date = extract['date']

        if datetime.now().date() > date.date():
            raise BotException('В расписании отображаются только будущие рейсы')

        if add_eleven_month() < date.date():
            raise BotException('Расписание составлено только на 11 месяцев '
                               'вперед от текущей даты')

        if self.user.get('last_rasp_request'):
            if src is None:
                src = self.user['last_rasp_request'].get('src')
            if dst is None:
                dst = self.user['last_rasp_request'].get('dst')

        if len(extract['cities']) > 0 and extract['src'] is None and extract['dst'] is None:
            if dst is None:
                dst = extract['cities'][0]
            elif src is None:
                src = extract['cities'][0]

        unknown_destination = extractor.is_unknown_destination(self.msg.text) or dst is None

        last_rasp_request = self.user.get('last_rasp_request') or {}
        if src is not None:
            last_rasp_request['src'] = src
        if dst is not None:
            last_rasp_request['dst'] = dst
        if last_rasp_request:
            self.user['last_rasp_request'] = last_rasp_request

        if src and unknown_destination:
            src_title = src
            try:
                src_morph = morph.parse(src)[0]
                src_morph = src_morph.inflect({'gent'})
                src_title = src_morph.word
            except:
                pass

            response = 'Лучшие предложения с вылетом из {0}:\n\n'.format(src_title.title())
            for dst in extractor.get_suggestions_for_src(src):
                response += "{0} от {1} руб.\n".format(dst.title(), random.randint(1000, 10000))

            await self.send(response.strip())
        elif src and dst and date:
            rasp_params = dict(
                src=src, dst=dst,
                date=date.strftime('%Y-%m-%d'),
                extra=dict(transport_types='plane')
            )
            if src == dst:
                await self.send('Пункты отправления и прибытия должны отличаться')
                return

            self.user['last_rasp_request'] = rasp_params
            rasp = await self.store.yandex_rasp.fetch(**rasp_params)

            results = dict()
            for item in rasp.get('threads'):
                try:
                    flight_id = item['thread']['number'].replace(' ', '')
                    if not flight_id.startswith('S7'):
                        continue

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
                await self.send(
                    'Не нашлось рейсов на {0} по маршруту {1} - {2}'.format(readable_date(date), src.title(),
                                                                            dst.title()))
        else:
            msg = ''
            if not (is_common_phrases and src is None and dst is None):
                msg = '{direction} нужно лететь? '
            await self.send(
                (msg + 'Напишите в свободной форме о вашем путешествии').format(
                    direction='Откуда' if src is None else 'Куда'
                )
            )

    def reset(self):
        self.cv = None
        self.parent.set_state(None)
        self.parent.user['last_rasp_request'] = None
