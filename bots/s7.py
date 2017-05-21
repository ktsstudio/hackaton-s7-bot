import random
from datetime import datetime

from roboman.exceptions import BotException
from tornkts.utils import to_int

from base.bot import BaseBot
from bots.subbot.buy import BuyBot
from bots.subbot.registration import RegistrationBot
from bots.subbot.search import SearchBot
from tools import extractor
from tools.extractor import QuestionType
from settings import options


# similarity = prepare_sim_func(FAQ, get_wv())


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

    def option_text(self, option):
        if self.is_telegram:
            return '/{}'.format(option)
        if self.is_vk:
            return '{}'.format(option)

    def parse_option_text(self, option, default=0):
        if self.is_telegram:
            if option.startswith('/'):
                return to_int(option[1:], default)
        if self.is_vk:
            return to_int(option, default)

    async def before_hook(self):
        self.user = await self.store.db.users.find_one({'external': self.msg.unique_key})

        if self.user is None:
            self.user = {
                'external': self.msg.unique_key,
                'last_use': to_int(datetime.now().timestamp()),
                'state': self.state
            }

        if not self.user.get('name') and not self.user.get('surname'):
            if self.is_telegram:
                msg_from = self.msg.extra.get('from')
                self.user['name'] = msg_from.get('first_name')
                self.user['surname'] = msg_from.get('last_name')
            elif self.is_vk:
                vk = await self.vk_user_get(self.msg.from_id)
                if vk:
                    self.user['name'] = vk.get('first_name')
                    self.user['surname'] = vk.get('last_name')

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
            return
        elif self.state == "registration":
            await self.run(RegistrationBot)
            return
        elif self.state == 'faq':
            questions = self.user.get('faq', {}).get('questions')

            option = self.parse_option_text(self.msg.text, 0)
            if option is not None:
                if questions is not None and not (0 < option <= len(questions)):
                    raise BotException('Введите число от 1 до {}'.format(len(questions)))
                else:
                    q_id = questions[option - 1]
                    q = await self.store.search.get(id=q_id)

                    await self.send(q['text'])
                    return

            self.user['faq'] = {}
            self.set_state(None)
            # return
        # else:
        is_common_phrases = await self.common_phrase()
        await self.process(is_common_phrases)

    async def process(self, is_common_phrases):
        text = self.msg.text
        question_type = extractor.detect_question(text)
        if question_type == QuestionType.SEARCH:
            return await self.process_search(is_common_phrases)
        elif question_type == QuestionType.REGISTRATION:
            return await self.process_registration(is_common_phrases)
        elif text.startswith('faq') or question_type == QuestionType.FAQ:
            self.msg.text = self.msg.text.replace('faq', '')
            return await self.process_faq(is_common_phrases)
        elif question_type == QuestionType.NONE:
            # TODO: rethink
            if is_common_phrases:
                return
            elif self.state is None:
                await self.send('Вы можете начать покупку билета с фразы, '
                                'например "Отправиться из Москвы в Казань."\n'
                                'Либо просто задайте интересующий вас вопрос.')
        else:
            raise Exception('unexpected question type')

    async def process_search(self, is_common_phrases):
        if options.debug:
            await self.send('Попытка заказать билет')
        await self.run(SearchBot, extra=dict(
            is_common_phrases=is_common_phrases
        ))

    async def process_registration(self, is_common_phrases):
        if options.debug:
            await self.send('Попытка регистрации на рейс')
        self.set_state("registration")
        await self.run(RegistrationBot)

    async def process_faq(self, is_common_phrases):
        # result = find_similar_faq(self.msg.text, FAQ, FAQ_DF, similarity)
        intro = 'Вот список наиболее подходящих вопросов:\n'

        result = await self.store.search.search(self.msg.text)
        ids = []
        response = []
        for i, r in enumerate(result):
            response.append('{}. {}'.format(self.option_text(i + 1), r['title']))
            ids.append(r['id'])
        response = '\n'.join(response)

        self.user['faq'] = {
            'questions': ids,
        }
        self.set_state('faq')

        outro = '\n\nЕсли вы не видите нужного вопроса, можете попробовать найти ответ на сайте https://www.s7.ru/info/faq/faq.dot'

        await self.send(intro + response + outro)

    async def buy_detector(self):
        text = set(extractor.tokenize(self.msg.text))

        if self.user.get('last_rasp_request') and self.user['last_rasp_request'].get('src') is not None and self.user['last_rasp_request'].get('dst') is not None:
            last_rasp_request = self.user['last_rasp_request']
            try:
                rasp = await self.store.yandex_rasp.fetch(**last_rasp_request)
            except:
                self.user['last_rasp_request'] = None
            else:
                for item in rasp.get('threads'):
                    number = item['thread']['number'].replace(' ', '').lower()

                    if number in text:
                        return item

        return False

    async def common_phrase(self):
        text = set(extractor.tokenize(self.msg.text))

        to_response = set()
        detect = {
            'greetings': ['привет', 'приветик', 'хай', 'здравствуйте', 'здравствуй', 'здарова', 'hi', 'hello',
                          'bonjour', 'start'],
            'thankyou': ['спасибо', 'спс', 'спася', 'благодарить']
        }
        responses = {
            'greetings': 'Hello',
            'thankyou': ['Всегда пожалуйста!', 'Всегда Ваш, S7.', 'Обращайтесь еще!', 'Всегда рады Вам помочь!']
        }

        for key, keywords in detect.items():
            for keyword in keywords:
                if keyword in text:
                    to_response.add(key)
                    break

        message = None
        for item in to_response:
            message = responses.get(item)
            if not message:
                continue

            if item == 'greetings':
                now = datetime.now()
                if 0 <= now.hour < 4:
                    message = 'Доброй ночи'
                elif 4 <= now.hour < 12:
                    message = 'Доброе утро'
                elif 12 <= now.hour < 18:
                    message = 'Добрый день'
                else:
                    message = 'Добрый вечер'
                message += '. Задайте свой вопрос или напишите, куда хотите полететь.'
                break

            if item == 'thankyou':
                message = random.choice(message)
                break

        if message:
            await self.send(message)

        return len(to_response) > 0
