from tornkts.base.server_response import ServerError
from tornkts.utils import json_loads

from base.handler import BaseHandler


class BuyHandler(BaseHandler):
    @property
    def get_methods(self):
        return {
            'info': self.info,
        }

    @property
    def post_methods(self):
        return {
            'addPassenger': self.add_passenger,
        }

    async def _get_user(self, buy_id):
        user = await self.store.db.users.find_one({'cv.buy_id': buy_id})
        if not user or not user.get('cv'):
            raise ServerError(ServerError.NOT_FOUND)

        return user

    async def _save_user(self, buy_id, user):
        await self.store.db.users.update_one({'cv.buy_id': buy_id}, {'$set': user}, upsert=True)

    async def info(self):
        buy_id = self.get_str_argument('buy_id')
        user = await self._get_user(buy_id)

        self.send_success_response(
            data={
                'flight': user.get('flight'),
                'from': {
                    'name': user.get('name'),
                    'surname': user.get('surname'),
                }
            }
        )

    async def add_passenger(self):
        buy_id = self.get_str_argument('buy_id')
        passengers = json_loads(self.get_argument('passengers'))
        passengers_names = []

        if not isinstance(passengers, list):
            raise ServerError(ServerError.BAD_REQUEST)

        user = await self._get_user(buy_id)

        cv = user['cv']
        if not cv.get('passengers'):
            cv['passengers'] = list()

        for passenger in passengers:
            cv['passengers'].append(passenger)

            passengers_names.append('{name} {surname}'.format(
                name=passenger.get('name'),
                surname=passenger.get('surname'),
            ))

        user['cv'] = cv
        await self._save_user(buy_id, user)

        self.send_success_response()
        self.finish()

        if len(passengers_names) > 0:
            bot = self.bot(user)
            await bot.send(
                '{users} {verb} на рейс\n\n'
                'Для просмотра всех пассажиров введите {all}\n'
                'Для заказа билетов напишите {yes}\n'
                'Для отмены покупки напишите {cancel}'.format(
                    all='Все' if bot.is_vk else '/all',
                    yes='Да' if bot.is_vk else '/ok',
                    cancel='Отмена' if bot.is_vk else '/cancel',
                    users=', '.join(passengers_names),
                    verb='зарегистрировался' if len(passengers_names) == 1 else 'зарегистрировались',
                )
            )
