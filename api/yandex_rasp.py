from urllib.parse import urlencode

from roboman.exceptions import BotException
from roboman.stores import BaseStore
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httputil import url_concat
from tornkts.utils import json_loads

client = AsyncHTTPClient()


class YandexRasp(BaseStore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs.get('api_key')

    async def place_code(self, query):
        params = {
            'lang': 'ru',
            'national_version': 'ru',
            'part': query,
            't_type_code': 'plane',
            'format': 'old'
        }

        url = url_concat('https://suggests.rasp.yandex.net/by_t_type', params)

        result = await self.store.cache.get(url)
        if not result:
            request = HTTPRequest(url)
            try:
                response = await client.fetch(request)
                result = json_loads(response.body)
                result = result[1][0][0]
                await self.store.cache.set(url, result)
            except:
                raise BotException('В городе `%s` нет аэропорта' % query)
        return result

    async def fetch(self, **kwargs):
        params = {
            'apikey': self.api_key,
            'from': (await self.place_code(kwargs.get('src'))),
            'to': (await self.place_code(kwargs.get('dst'))),
            'format': 'json',
            'lang': 'ru',
            'date': kwargs.get('date'),
            'page': 1,
        }

        params.update(kwargs.get('extra', {}))

        url = url_concat('https://api.rasp.yandex.net/v1.0/search/', params)

        result = await self.store.cache.get(url)
        if not result:
            request = HTTPRequest(url)
            try:
                response = await client.fetch(request)
                result = json_loads(response.body)
                await self.store.cache.set(url, result)
            except:
                raise BotException('Ошибка в получении расписания')
        return result
