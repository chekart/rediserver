import pytest
from .embedded import EmbeddedRedis, EmbeddedRedisSession


@pytest.fixture(scope='session')
def embedded_redis_server():
    with EmbeddedRedis() as socket_file:
        yield socket_file


@pytest.fixture(scope='function')
def embedded_redis(embedded_redis_server):
    with EmbeddedRedisSession(
            socket_file=embedded_redis_server,
            db=0) as redis_proxy:
        yield redis_proxy
