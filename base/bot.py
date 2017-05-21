from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httputil import url_concat
from tornkts.utils import json_loads

from roboman.bot.bot import BaseBot as RobomanBaseBot

client = AsyncHTTPClient()


class BaseBot(RobomanBaseBot):
    async def vk_user_get(self, user_id):
        url = 'https://api.vk.com/method/users.get'
        url = url_concat(url, {'user_id': user_id, 'v': '5.52'})

        result = await client.fetch(HTTPRequest(url=url))
        result = json_loads(result.body)

        try:
            return result['response'][0]
        except Exception as e:
            return False
