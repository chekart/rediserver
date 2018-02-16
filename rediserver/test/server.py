import os
import inspect

from copy import deepcopy
from tempfile import TemporaryDirectory
from functools import wraps

from ..server import run_threaded


class RedisServer:
    def __init__(self):
        self.stop_loop = None
        self.tempdir = None
        self.thread = None

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper

    def __enter__(self):
        assert self.thread is None

        self.tempdir = TemporaryDirectory()
        socket_file = os.path.join(self.tempdir.name, 'redis.sock')
        redis, self.thread, self.stop_loop = run_threaded(unix_domain_socket=socket_file)

        class RedisProxy:
            def __init__(self):
                class Ext:
                    pass
                self.ext = Ext()

            def extend(self, attr, value):
                setattr(self.ext, attr, value)

            @property
            def dict(self):
                return deepcopy(redis.keys)

            def __len__(self):
                return len(redis.keys)

            def __getitem__(self, key):
                if isinstance(key, str):
                    key = key.encode()
                return deepcopy(redis.keys[key])

            @property
            def sock(self):
                return socket_file

        return RedisProxy()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_loop()
        self.thread.join()
        self.tempdir.cleanup()

        self.stop_loop = None
        self.tempdir = None
        self.thread = None


def local_redis(func=None):
    if func is None:
        return RedisServer()

    if inspect.isfunction(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with RedisServer():
                return func(*args, **kwargs)

        return wrapper

    raise ValueError()
