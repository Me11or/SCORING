# -*- coding: utf-8 -*-
import redis
import time
import logging

MAX_RETRY = 3
RETRY_DELAY = 0.1


def retry_whith_raise_control(raise_on_failure=True):
    def retry_decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for i in range(MAX_RETRY):
                try:
                    return func(*args, **kwargs)
                except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                    last_exception = e
                    time.sleep(RETRY_DELAY)

            if last_exception is not None:
                msg = 'Exceeded the maximum number of connection attempts(%d). Function %s' % (MAX_RETRY, func)
                logging.exception(msg, exc_info=last_exception)

            if raise_on_failure:
                raise last_exception

        return wrapper

    return retry_decorator


class Store(object):

    client = None
    params = {}

    def __init__(self, **kwargs):
        self.params = kwargs

    @retry_whith_raise_control(raise_on_failure=True)
    def connect(self):
        self.client = redis.Redis(**self.params)
        self.client.ping()

    def close(self):
        self.client.close()

    @retry_whith_raise_control(raise_on_failure=True)
    def set(self, key, *values):
        return self.client.sadd(key, *values)

    @retry_whith_raise_control(raise_on_failure=False)
    def cache_set(self, key, value, expire):
        return self.client.set(key, value, ex=expire)

    @retry_whith_raise_control(raise_on_failure=True)
    def get(self, key):
        return self.client.smembers(key)

    @retry_whith_raise_control(raise_on_failure=False)
    def cache_get(self, key):
        return self.client.get(key)
