import copy
import datetime
import os
import random

import imgkit
import pymongo
from roboman.bot.bot import BaseBot
from tornado import template

from tools import extractor

INIT = 0
FLIGHT_CHOOSE = 1
PLANE_PLACES = 2
PLACES_CHOSEN = 3
CONFIRMATION = 4

PLACE_NOT_FOUND = object()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

A319_PLACES = {
    "A": {
        '3': 1, '23': None, '8': 1, '1': 1, '4': None, '22': None, '21': None, '20': None, '12': 1, '11': 1, '7': 1,
        '15': None, '16': None, '17': None, '9': 1, '18': None, '5': 1, '2': 1, '6': 1, '14': None, '19': 1,
        '13': None, '10': 1, '24': 1},
    "B": {'3': None, '23': 1, '8': None, '1': None, '4': None, '22': 1, '21': 1, '20': 1, '12': 1, '11': 1, '7': 1,
          '15': 1, '16': None, '17': 1, '9': None, '18': None, '5': 1, '2': None, '6': 1, '14': None, '19': None,
          '13': 1, '10': 1, '24': 1},
    "C": {'3': 1, '23': 1, '8': 1, '1': 1, '4': 1, '22': 1, '21': None, '20': 1, '12': 1, '11': 1, '7': 1, '15': 1,
          '16': None, '17': 1, '9': 1, '18': 1, '5': 1, '2': 1, '6': 1, '14': 1, '19': None, '13': None, '10': None,
          '24': 1},
    "D": {'3': 1, '23': None, '8': None, '1': 1, '4': None, '22': None, '21': None, '20': None, '12': 1, '11': 1,
          '7': None, '15': 1, '16': None, '17': None, '9': None, '18': 1, '5': 1, '2': 1, '6': None, '14': None,
          '19': None, '13': 1, '10': None, '24': None},
    "E": {'3': 1, '23': None, '8': 1, '1': None, '4': 1, '22': 1, '21': 1, '20': 1, '12': None, '11': None, '7': None,
          '15': 1, '16': None, '17': 1, '9': 1, '18': None, '5': None, '2': None, '6': 1, '14': None, '19': None,
          '13': None, '10': 1, '24': None},
    "F": {'3': None, '23': 1, '8': None, '1': None, '4': 1, '22': None, '21': None, '20': 1, '12': None, '11': None,
          '7': 1, '15': None, '16': None, '17': 1, '9': None, '18': 1, '5': None, '2': 1, '6': None, '14': None,
          '19': 1, '13': 1, '10': None, '24': 1}
}


class RegistrationBot(BaseBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.r_state = INIT
        self.r_flight_id = None
        self.r_flight = None
        self.r_cv = None
        self.r_cv_id = None

    async def get_or_create_flight(self, flight):
        db_flight = await self.store.db.flights.find_one({
            "thread.number": flight['thread']['number'],
            "departure": flight['departure']
        })

        if db_flight is None:
            copy_flight = copy.deepcopy(flight)
            copy_flight["places"] = A319_PLACES

            res = await self.store.db.flights.insert_one(copy_flight)
            copy_flight["_id"] = res.inserted_id
        else:
            return db_flight

        return copy_flight

    async def send_chosen_flight_message(self, flight, cv):
        date = datetime.datetime.strptime(flight['departure'], "%Y-%m-%d %H:%M:%S")
        await self.send("Подождите, я подготавливаю информацию о рейсе")
        image_path = self.create_image(self.number_as_rows(flight['places']))

        await self.send_image(image_path)

        message = ["Рейс {flight_number} {from_} - {to} {date}\n".format(
            flight_number=flight['thread']['number'],
            from_=flight['from']['title'],
            to=flight['to']['title'],
            date=date.strftime("%d.%m %H:%M")
        ), "Свободные места обозначены на картинке зеленым.\n", ]

        if cv.get('passengers') and len(cv.get('passengers')) > 1:
            passengers = cv.get('passengers')
            message.append("Вам необходимо зарегистрировать {} пассажиров.".format(len(passengers)))
            message.append("Введите места в формате «ряд, буква» (например 2E, 2С)")
            message.append('Если Вам неважно, на каком месте вы проведете полет, просто введите "Любые".')
        else:
            message.append("Введите место в формате «ряд, буква» (например 2Е).")
            message.append('Если Вам неважно, на каком месте вы проведете полет, просто введите "Любое".')

        # near_window, near_pass, privileges, other = self.extract_available_places(flight['places'])
        #
        # message.append("У окна: {}".format(", ".join(near_window)))
        # message.append("У прохода: {}".format(", ".join(near_pass)))
        # message.append("Повышенного комфорта: {}".format(", ".join(privileges)))
        # message.append("Остальные: {}".format(", ".join(other)))

        await self.send("\n".join(message))

        self.r_state = PLANE_PLACES
        self.r_flight_id = flight['_id']
        self.r_cv_id = cv['_id']

    async def choose_flight(self):
        try:
            number = int(self.msg.text)
        except ValueError:
            await self.send("Попробуте еще раз, укажите номер рейса по порядку")
            return
        cvs = await self.get_not_registered_flights()

        if number < 1:
            await self.send("Рейса с таким номером нет")
            return
        try:
            cv = cvs[number - 1]
        except IndexError:
            await self.send("Рейса с таким номером нет")
            return

        flight = await self.get_or_create_flight(cv['flight'])
        await self.send_chosen_flight_message(flight, cv=cv)

    async def show_flights(self):
        cvs = await self.get_not_registered_flights()

        if not cvs:
            await self.send("У Вас нет билетов с открытой регистрацией")
            self.r_state = INIT
            self.parent.set_state(None)
            return

        if len(cvs) == 1:
            flight = await self.get_or_create_flight(cvs[0]['flight'])
            await self.send_chosen_flight_message(flight, cv=cvs[0])
            await self.send('Напишите "Отмена", чтобы прекратить процедуру регистрации')
            return

        i = 1
        flight_rows = []
        for cv in cvs:
            date = datetime.datetime.strptime(cv['flight']['departure'], "%Y-%m-%d %H:%M:%S")

            flight_rows.append("{number}. Рейс {flight_number} {from_} - {to} {date}".format(
                number=i,
                flight_number=cv['flight']['thread']['number'],
                from_=cv['flight']['from']['title'],
                to=cv['flight']['to']['title'],
                date=date.strftime("%d-%m %H:%M")
            ))
            i += 1

        await self.send(
            "Вы можете зарегистрироваться на данные рейсы:\n\n" +
            "\n".join(flight_rows) + "\n\n" +
            "Выберите рейс, указав номер по порядку (1...{})".format(i - 1)
        )

        await self.send('Напишите "Отмена", чтобы прекратить процедуру регистрации')

        self.r_state = FLIGHT_CHOOSE

    def generate_rand_place(self, num):
        places = []
        i = 0
        while True:
            free_places = self.get_free_places(self.r_flight['places'])
            bad_places = list(filter(lambda x: x.startswith("B") or x.startswith("E"), free_places))
            if bad_places:
                free_places = bad_places
            text = free_places.pop(random.randint(0, len(free_places)))

            if text not in places:
                places.append(text)
                i += 1

            if i == num: break

        return places

    async def choose_many_places(self):
        passengers = self.r_cv.get('passengers')
        reg_places = self.r_cv.get('reg_places')
        if not reg_places:
            reg_places = []
        num_to_reg = len(passengers) - len(reg_places)
        if self.match_command("любые"):
            places_words = self.generate_rand_place(num_to_reg)
        else:
            places_words = extractor.tokenize(self.msg.text, disable_normal=True)
        need_to_reg = []
        engaged = []
        i = 0
        for word in places_words:
            if i >= num_to_reg:
                break
            num, let = self.valid_place_word(word.upper())
            if num and word.upper() not in reg_places and word.upper() not in need_to_reg:
                numbers = self.r_flight['places'].get(let)

                if numbers:
                    place = numbers.get(str(num), PLACE_NOT_FOUND)

                    if place is not PLACE_NOT_FOUND:
                        if place is None:
                            need_to_reg.append(word.upper())
                            i += 1
                        else:
                            engaged.append(word.upper())

        if need_to_reg:
            for place in need_to_reg:
                self.r_flight['places'][place[-1]][str(place[:-1])] = 1

            await self.store.db.flights.update_one(
                {'_id': self.r_flight_id},
                {'$set': self.r_flight},
                upsert=True,
            )

            if i >= num_to_reg:
                self.r_cv['registered'] = True
            self.r_cv['reg_places'] = reg_places + need_to_reg

            await self.store.db.reserving.update_one(
                {'_id': self.r_cv['_id']},
                {'$set': self.r_cv},
                upsert=True,
            )

            if (num_to_reg - i) > 0:
                end = "а" if 5 > num_to_reg - i > 1 else "о" if num_to_reg - i == 1 else ""
                await self.send(
                    "Вы зарегистрировали места: {}".format(", ".join(reg_places + need_to_reg)) + "\n" +
                    "Осталось зарегистрировать {} мест{}".format(num_to_reg - i, end)
                )
                if engaged:
                    if len(engaged) == 1:
                        await self.send(
                            "Место {} уже занято".format(engaged[0])
                        )
                    else:
                        await self.send(
                            "Места {} уже заняты".format(", ".join(engaged))
                        )
                return

            date = datetime.datetime.strptime(self.r_flight['departure'], "%Y-%m-%d %H:%M:%S")
            await self.send("Вы зарегистрировались на рейс {}. Ваши места: {}. Приятного полета!".format(
                "{number} {from_} - {to} {date}".format(
                    number=self.r_flight['thread']['number'],
                    from_=self.r_flight['from']['title'],
                    to=self.r_flight['to']['title'],
                    date=date.strftime("%d-%m %H:%M")
                ),
                ", ".join(reg_places + need_to_reg)
            ))
            await self.send("Используйте данные штрих-коды для получения посадочного талона в аэропорту")
            for passenger in passengers:
                await self.send_image(os.path.join(BASE_DIR, "data/shtrihcode.png"))
            self.r_state = INIT
            self.parent.set_state(None)
            return
        else:
            if engaged:
                if len(engaged) == 1:
                    await self.send(
                        "Место {} уже занято".format(engaged[0])
                    )
                else:
                    await self.send(
                        "Места {} уже заняты".format(", ".join(engaged))
                    )
            else:
                await self.send("Введите места в правильном формате: «ряд, буква» (например 2Е)")
            return

    def valid_place_word(self, word):
        try:
            num, let = int(word[:-1]), word[-1]
            return num, let
        except:
            return None, None

    async def choose_place(self):
        if len(self.r_cv.get("passengers", [])) != 1:
            await self.choose_many_places()
            return
        if self.match_command("любое"):
            free_places = self.get_free_places(self.r_flight['places'])
            bad_places = list(filter(lambda x: x.startswith("B") or x.startswith("E"), free_places))
            if bad_places:
                free_places = bad_places
            text = free_places.pop(random.randint(0, len(free_places)))
        else:
            text = self.msg.text
        try:
            num, let = int(text[:-1]), text[-1]
        except:
            await self.send("Укажите место в правильном формате")
            return

        numbers = self.r_flight['places'].get(let)

        if numbers:
            place = numbers.get(str(num), PLACE_NOT_FOUND)

            if place is not PLACE_NOT_FOUND:
                if place is None:
                    self.r_flight['places'][let][str(num)] = 1
                    await self.store.db.flights.update_one(
                        {'_id': self.r_flight_id},
                        {'$set': self.r_flight},
                        upsert=True,
                    )
                    self.r_cv['registered'] = True

                    await self.store.db.reserving.update_one(
                        {'_id': self.r_cv['_id']},
                        {'$set': self.r_cv},
                        upsert=True,
                    )
                    date = datetime.datetime.strptime(self.r_flight['departure'], "%Y-%m-%d %H:%M:%S")
                    await self.send("Вы зарегистрировались на рейс {}. Ваше место - {}. Приятного полета!".format(
                        "{number} {from_} - {to} {date}".format(
                            number=self.r_flight['thread']['number'],
                            from_=self.r_flight['from']['title'],
                            to=self.r_flight['to']['title'],
                            date=date.strftime("%d-%m %H:%M")
                        ),
                        text
                    ))
                    self.r_state = INIT
                    self.parent.set_state(None)
                    await self.send("Используйте этот штрих-код для получения посадочного талона в аэропорту")
                    await self.send_image(os.path.join(BASE_DIR, "data/shtrihcode.png"))
                    return
                else:
                    await self.send("Это место занято")
                    return

        await self.send("Не найдено место с таким номером")

    async def get_not_registered_flights(self):
        return await self.store.db.reserving.find(
            {'user_id': self.parent.user['_id'], "registered": False},
            sort=[('id', pymongo.ASCENDING), ]
        ).to_list(
            length=100
        )

    async def before_hook(self):
        self.r_state = self.parent.user.get("r_state") or INIT
        self.r_flight_id = self.parent.user.get('r_flight')
        self.r_cv_id = self.parent.user.get('r_cv')
        if self.r_state not in (INIT, FLIGHT_CHOOSE):
            self.r_flight = await self.store.db.flights.find_one({"_id": self.r_flight_id})
            self.r_cv = await self.store.db.reserving.find_one({"_id": self.r_cv_id})

    async def after_hook(self):
        user = self.parent.user
        user['r_state'] = self.r_state
        user['r_flight'] = self.r_flight_id
        user['r_cv'] = self.r_cv_id

        await self.store.db.users.update_one(
            {'external': self.msg.unique_key},
            {'$set': user},
            upsert=True,
        )

    async def hook(self):
        if self.match_command("отмена"):
            self.parent.set_state(None)
            self.r_state = INIT
            self.r_flight_id = None
            self.r_cv_id = None
            await self.send("Регистрация отменена")
            return
        if self.r_state == INIT:
            await self.show_flights()
            return
        elif self.r_state == FLIGHT_CHOOSE:
            await self.choose_flight()
            return
        elif self.r_state == PLANE_PLACES:
            await self.choose_place()
            return

        await self.send("Произошла ошибка")
        self.r_state = INIT
        self.r_flight = None

    def extract_available_places(self, places):
        places_near_window = [str(n[0]) + "A" for n in filter(lambda x: x[1] is None, places["A"].items())]
        places_near_window += [str(n[0]) + "F" for n in filter(lambda x: x[1] is None, places["F"].items())]
        places_near_window = sorted(places_near_window, key=lambda x: int(x[:-1]))
        places_near_pass = [str(n[0]) + "C" for n in filter(lambda x: x[1] is None, places["C"].items())]
        places_near_pass += [str(n[0]) + "D" for n in filter(lambda x: x[1] is None, places["D"].items())]
        places_near_pass = sorted(places_near_pass, key=lambda x: int(x[:-1]))

        privileges = []

        for key in places:
            if places[key]["1"] is None:
                privileges.append("1" + key)
            if places[key]["11"] is None:
                privileges.append("11" + key)
        privileges = sorted(privileges, key=lambda x: int(x[:-1]))

        other = [str(n[0]) + "B" for n in filter(lambda x: x[1] is None, places["B"].items())]
        other += [str(n[0]) + "E" for n in filter(lambda x: x[1] is None, places["E"].items())]

        for pr in privileges:
            try:
                other.remove(pr)
            except ValueError:
                pass

        other = sorted(other, key=lambda x: int(x[:-1]))

        return places_near_window, places_near_pass, privileges, other

    def create_image(self, places):
        loader = template.Loader(os.path.join(BASE_DIR, "data"))
        t = loader.load("plane_scheme.html")
        rendered = t.generate(places=places, base_path=BASE_DIR).decode('utf-8')
        filename = '/tmp/%s.png'.format(datetime.datetime.utcnow())
        try:
            imgkit.from_string(
                string=rendered,
                output_path=filename,
                options={
                    "quiet": "",
                    'crop-h': '835',
                    'crop-w': '244',
                    'encoding': "UTF-8"
                },
                config=imgkit.config(wkhtmltoimage="/usr/local/bin/wkhtmltoimage")
            )
        except:
            pass
        return filename

    @staticmethod
    def number_as_rows(places):
        numbers = {}
        for let, nums in places.items():
            for num, engaged in nums.items():
                numbers.setdefault(num, [])
                numbers[num].append((let, engaged))

        numbers_list = []
        for numb, lets in sorted(numbers.items(), key=lambda x: int(x[0])):
            numbers_list.append((numb, sorted(lets, key=lambda x: x[0])))

        return numbers_list

    def get_free_places(self, places):
        free = []
        for key, numbers in places.items():
            for num, engaged in numbers.items():
                if not engaged:
                    free.append(str(num) + key)
        return free
