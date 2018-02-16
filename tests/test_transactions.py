import pytest
from redis.exceptions import WatchError


def test_ok(redis):
    client = redis.ext.client

    pipeline = client.pipeline()
    pipeline.set('test', 1)
    pipeline.sadd('test2', 2)
    pipeline.execute()
    assert client.get('test') == b'1'
    assert redis.dict == {b'test': b'1', b'test2': {b'2'}}


def test_ok_lowlevel(redis):
    client = redis.ext.client

    assert client.execute_command('MULTI') == b'OK'
    assert client.get('test') == b'QUEUED'
    # Redis client uses response hooks to bool this
    assert not client.set('test', 1)
    assert redis.dict == {}
    assert client.execute_command('EXEC') == [None, b'OK']
    assert redis.dict == {b'test': b'1'}


def test_ok_response(redis):
    client = redis.ext.client
    client.sadd('test', 1, 2)
    client.sadd('test2', 2, 3, 4)
    assert client.pipeline().scard('test').scard('test2').execute() == [2, 3]


def test_back_to_normal_state(redis):
    client = redis.ext.client
    result = client.pipeline().set('test', 1).execute()
    assert result
    result = client.sadd('test2', 1, 2)
    assert result == 2


def test_watch(redis):
    client = redis.ext.client
    client2 = redis.ext.new_client()

    client.set('watched', 1)

    pipeline = client.pipeline()
    assert pipeline.watch('watched')
    pipeline.multi()
    pipeline.get('watched')
    pipeline.set('key', 1)

    assert client2.set('watched', 2)

    with pytest.raises(WatchError, match='Watched variable changed'):
        pipeline.execute()

    assert redis.dict == {b'watched': b'2'}
