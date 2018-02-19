import redis

from rediserver.test.embedded import EmbeddedRedisSession


def test_connected(embedded_redis):
    client = redis.StrictRedis(unix_socket_path=embedded_redis.sock)
    client.set('test', 'value')
    assert client.get('test') == b'value'


def test_flush(embedded_redis_server):
    client = redis.StrictRedis(unix_socket_path=embedded_redis_server)
    client.set('test', 'some value')

    with EmbeddedRedisSession(embedded_redis_server):
        assert client.get('test') is None
        client.set('test', 'value')
        assert client.get('test') == b'value'

    assert client.get('test') is None

