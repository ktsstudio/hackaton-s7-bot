import tornado_mysql
from roboman.stores import BaseStore


class SearchStore(BaseStore):
    def __init__(self, host, port, index_name='objects', **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.index_name = index_name
        self.conn = None

    async def connect(self):
        self.conn = await tornado_mysql.connect(host=self.host,
                                                port=self.port,
                                                db=self.index_name,
                                                charset='utf8')

    async def disconnect(self):
        if self.conn:
            self.conn.close()

    async def search(self, text, limit=5, include_text=False):
        fields = ['id', 'title']
        if include_text:
            fields.append('text')

        await self.conn.connect()
        cur = self.conn.cursor()
        q = 'SELECT {} FROM {} WHERE MATCH(\'"{}"/1\') LIMIT {} OPTION field_weights=(title=2,text=1)'.format(
            ','.join(fields),
            self.index_name,
            text,
            limit
        )
        print(q)
        await cur.execute(q)

        result = []
        for row in cur:
            d = {
                'id': row[0],
                'title': row[1],
            }
            if include_text:
                d['text'] = row[2]
            result.append(d)

        cur.close()
        return result

    async def get(self, id):
        await self.conn.connect()
        cur = self.conn.cursor()
        q = 'SELECT id, title, text FROM {} WHERE id = {} LIMIT 1'.format(
            self.index_name,
            id
        )
        print(q)
        await cur.execute(q)

        result = None
        for row in cur:
            result = {
                'id': row[0],
                'title': row[1],
                'text': row[2],
            }
            break

        cur.close()
        return result
