import pytest
import redis as redis_client

pytest_plugins = 'rediserver.test.pytest',


@pytest.fixture(scope='function')
def redis(local_redis):
    local_redis.extend('client', redis_client.StrictRedis(unix_socket_path=local_redis.sock))
    return local_redis
