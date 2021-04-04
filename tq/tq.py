import os
import redis
from rq import Worker, Queue, Connection
import constants
import pymysql.cursors
import json
from redis import Redis
from urllib.parse import urlparse
from functions import *


listen = ['default']

server = os.environ.get('REDIS_HOST')

redis_url = os.getenv('REDISTOGO_URL', 'redis://'+server+':6379/0')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
