import os
from confman import define, options

define('debug', default=False, type=bool, help='debug')

define('worker', type=dict, default={
    'broker_url': 'http://127.0.0.1:5555',
    'bucket': 'main',
    'access_token': ''
})

define('broker', type=dict, default={
    'host': '127.0.0.1',
    'port': 5555
})

define('messengers', type=dict, default={
    'vk': {},
    'telegram': {}
})

define('api', type=dict, default={
    'host': '127.0.0.1',
    'port': 8090,
    'order_form_url': 'http://127.0.0.1:8080/',
})

define('bot', type=dict, default={
    'api': {}
})

CONF = os.getenv('CONF', '/etc/s7-bot/s7-bot.yaml')
if os.path.exists(CONF):
    options.read_config(CONF)
