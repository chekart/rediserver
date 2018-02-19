import os
import docker
import redis

from tempfile import TemporaryDirectory


REDIS_CONF = os.path.join(os.path.dirname(__file__), 'conf/redis.conf')


class EmbeddedRedis:
    def __init__(self):
        self.client = docker.from_env()
        self.container = None
        self.tempdir = None

    def start(self):
        assert self.container is None
        self.tempdir = TemporaryDirectory()
        socket_file = os.path.join(self.tempdir.name, 'redis.sock')
        self.container = self.client.containers.run(
            'redis', detach=True, auto_remove=True,
            entrypoint=['redis-server', '/etc/redis/redis.conf'],
            volumes={
                REDIS_CONF: {'bind': '/etc/redis/redis.conf', 'mode': 'ro'},
                self.tempdir.name: {'bind': '/run/', 'mode': 'rw'},
        })
        return socket_file

    def stop(self):
        assert self.container
        self.container.stop()
        self.tempdir.cleanup()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class EmbeddedRedisSession:
    def __init__(self, socket_file, db=0):
        self.db = db
        self.socket_file = socket_file

    def __enter__(self):
        assert self.socket_file
        socket_file = self.socket_file

        class RedisProxy:
            def __init__(self):
                class Ext:
                    pass
                self.ext = Ext()

            def extend(self, attr, value):
                setattr(self.ext, attr, value)

            @property
            def dict(self):
                raise NotImplementedError()

            def __len__(self):
                raise NotImplementedError()

            def __getitem__(self, key):
                raise NotImplementedError()

            @property
            def sock(self):
                return socket_file

        client = redis.StrictRedis(unix_socket_path=self.socket_file, db=self.db)
        client.flushdb()

        return RedisProxy()

    def __exit__(self, exc_type, exc_val, exc_tb):
        client = redis.StrictRedis(unix_socket_path=self.socket_file, db=self.db)
        client.flushdb()
