import uuid
from collections import OrderedDict
from datetime import datetime

from dateutil.parser import parse
from tornkts.utils import to_int
from roboman.bot.bot import BaseBot
from tools import extractor
from tools.extractor import morph, tokenize, flight_cost


class BuyBot(BaseBot):
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

    async def before_hook(self):
        self.cv = self.parent.user.get('cv') or {}

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

        if self.match_command(self.confirm_message) and len(self.cv_skipped_fields) == 0:
            await self.payment_and_approve()
            return

        if self.cv['attempt'] == 0:
            await self.send(
                """
Введите свои данные (ФИО, дату рождения, паспортные данные).
Дату рождения нужно в вводить в формате день.месяц.год (например 01.04.1994), а паспорт 10 цифр подряд
Для отмены покупки напишите {0} 
                """.format(self.cancel_message)
            )
        elif self.cv['attempt'] == 1:
            self.cv.update(extractor.cv(self.msg.text))
            await self.send('Ваши данные\n' + self.cv_as_str())

            if len(self.cv_skipped_fields) == 0:
                await self.send(
                    """
Проверьте правильность заполнения анкеты, если все хорошо, напишите {0}
Для редактирования отправьте название поля и новое значение. Например: Фамилия Иванов 
                    """.format(self.confirm_message)
                )
            else:
                await self.send(
                    """
Не все поля удалось заполнить, дозаполните анкету.
Просто отправляйте название поля и новое значение. Например: Фамилия Иванов
                    """
                )
        else:
            errors = []
            lines = self.msg.text.split('\n')
            for line in lines:
                line = line.strip()
                for title, key in self.cv_fields(reverse=True).items():
                    if line.lower().startswith(title.lower()):
                        line = line[len(title) + 1:].strip()
                        error, line = self.validate_field(key, line)

                        if not error:
                            self.cv[key] = line
                        else:
                            errors.append(error)

            if len(errors) > 0:
                await self.send('\n'.join(errors))
            await self.send('Ваши данные\n' + self.cv_as_str())
            if len(self.cv_skipped_fields) == 0:
                await self.send(
                    """
Проверьте правильность заполнения анкеты, если все хорошо, напишите {0} 
                    """.format(self.confirm_message)
                )

    @property
    def cv_skipped_fields(self):
        result = []
        for key in self.cv_fields():
            if not self.cv.get(key):
                result.append(key)
        return result

    def cv_fields(self, reverse=False):
        fields = OrderedDict()
        fields['surname'] = 'Фамилия'
        fields['name'] = 'Имя'
        fields['patronymic'] = 'Отчество'
        fields['sex'] = 'Пол'
        fields['birthday'] = 'Дата рождения'
        fields['passport'] = 'Паспорт'

        if reverse:
            reverse_fields = OrderedDict()
            for key, value in fields.items():
                reverse_fields[value] = key
            fields = reverse_fields

        return fields

    def cv_as_str(self):
        result = []

        for key in self.cv_fields():
            value = self.cv.get(key)
            if key == 'sex':
                if value == 'm':
                    value = 'мужской'
                elif value == 'f':
                    value = 'женский'

            result.append('{0}: {1}'.format(self.cv_fields()[key], value if value else ''))

        return '\n'.join(result).strip()

    def validate_field(self, key, value):
        error = False
        if key == 'passport':
            if len(value) != 10 or to_int(value) is None:
                error = 'Номер паспорта должен состоять из 10 цифр'
        elif key == 'sex':
            value = {
                'мужской': 'm',
                'женский': 'f'
            }.get(value.lower())

            if not value:
                error = 'Введите корректное значение пола (мужской или женский)'
        elif key == 'birthday':
            try:
                parse(value, dayfirst=True)
            except:
                error = 'Дата рождения имеет неверный формат'

        return error, value

    async def payment_and_approve(self):
        flight = self.parent.user.get('flight')
        if flight:
            cost = flight_cost(flight)
        else:
            cost = 0

        await self.send(
            """
К демо-оплате {cost} ₽
Перейдите в демо-платежную систему по демо-ссылке: https://www.s7.ru/?{hash}
            """.format(cost=cost, hash=uuid.uuid4().hex)
        )

        self.cv['flight'] = flight
        await self.store.db.reserving.insert_one(self.cv)

        await self.send('Оплата произведена\nСчастливого пути!')
        self.reset()

    def reset(self):
        self.cv = None
        self.parent.set_state(None)
