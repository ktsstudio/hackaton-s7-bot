from tornkts import utils
from tornkts.handlers import BaseHandler as TornKTSHandler

from roboman.bot.message import Message


class BaseHandler(TornKTSHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self._payload = None

    def bot(self, user):
        source, from_id = user.get('external', '').split(':')

        msg = Message(source=source, from_id=from_id)
        return self.settings['worker'].bot_instance(msg)

    def get_argument(self, name, default=TornKTSHandler._ARG_DEFAULT, strip=True, **kwargs):
        if self.request.method == 'POST':
            if self._payload is None:
                try:
                    self._payload = utils.json_loads(self.request.body.decode())
                except:
                    pass
            if self._payload and name in self._payload:
                return self._payload[name]
            else:
                return super(BaseHandler, self).get_argument(name, default, strip)
        else:
            return super(BaseHandler, self).get_argument(name, default, strip)

    @property
    def store(self):
        return self.settings['worker'].store
