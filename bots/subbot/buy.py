import datetime

from tornado import gen
from tornado.httputil import url_concat
from settings import options
from roboman.bot.bot import BaseBot
from tools.extractor import flight_cost
import uuid


class BuyBot(BaseBot):
    @property
    def confirm_message(self):
        if self.is_telegram:
            return '/ok'
        if self.is_vk:
            return 'Да'

    @property
    def all_message(self):
        if self.is_telegram:
            return '/all'
        if self.is_vk:
            return 'Все'

    @property
    def cancel_message(self):
        if self.is_telegram:
            return '/cancel'
        if self.is_vk:
            return 'Отмена'

    async def before_hook(self):
        self.cv = self.parent.user.get('cv') or {
            'flight': self.parent.user.get('flight'),
        }

        if 'attempt' not in self.cv:
            self.cv['attempt'] = 0
        else:
            self.cv['attempt'] += 1

    async def after_hook(self):
        self.parent.user['cv'] = self.cv

    async def hook(self):
        if self.match_command(self.cancel_message):
            self.reset()
            await self.send('Вы отменили покупку')
            return
        elif self.match_command(self.all_message):
            passengers = self.cv.get('passengers', [])
            msg = []
            for i in range(len(passengers)):
                msg.append('{i}. {name} {surname}'.format(i=i + 1, **passengers[i]))

            if len(msg) > 0:
                await self.send('\n'.join(msg))
            else:
                await self.send('Пока еще никто не зарегистрировался')
            return
        elif self.match_command(self.confirm_message):
            await self.payment_and_approve()
            return
        elif self.cv['attempt'] == 0:
            url = options.api['order_form_url']
            self.cv['buy_id'] = uuid.uuid4().hex

            url = url_concat(url, {'buy_id': self.cv['buy_id']})

            await self.send(
                'Заполните данные по ссылке: {url}\n\nЭту ссылку можно отправить всем, с кем летите\n\n'
                'Для отмены покупки напишите {cancel}'.format(
                    url=url,
                    cancel=self.cancel_message
                )
            )
        else:
            await self.send(
                'Для просмотра всех пассажиров напишите {all}\n'
                'Для заказа билетов напишите {confirm}\n'
                'Для отмены покупки напишите {cancel}'.format(
                    all=self.all_message,
                    confirm=self.confirm_message,
                    cancel=self.cancel_message
                )
            )

    async def payment_and_approve(self):
        flight = self.cv.get('flight')
        if flight:
            price = flight_cost(flight)
        else:
            price = 0

        passengers = self.cv.get('passengers', [])
        count = len(passengers)
        cost = price * count

        await self.send(
            'К демо-оплате {price} x {count} = {cost} ₽\n'
            'Перейдите в демо-платежную систему по демо-ссылке: https://www.s7.ru/?{hash}'.format(
                price=price,
                cost=cost,
                count=count,
                hash=uuid.uuid4().hex
            )
        )

        self.cv['flight'] = flight
        self.cv['user_id'] = self.parent.user['_id']
        self.cv['registered'] = False
        await self.store.db.reserving.insert_one(self.cv)

        await gen.sleep(5)

        await self.send('Оплата произведена\nСчастливого пути!')

        date = datetime.datetime.strptime(self.cv['flight']['departure'], "%Y-%m-%d %H:%M:%S")

        if date <= datetime.datetime.now() + datetime.timedelta(hours=24):
            await self.send('Также Вы можете зарегистрироваться на рейс в любой момент,'
                            ' для этого введите "Регистрация".')
        else:
            await self.send('Электронная регистрация на рейс будет доступна за 24 часа до вылета.')
        self.reset()

    def reset(self):
        self.cv = None
        self.parent.set_state(None)
        self.parent.user['last_rasp_request'] = None
