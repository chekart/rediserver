import pytest
from redis.exceptions import ResponseError


def test_empty(redis):
    assert redis.dict == {}


def test_set(redis):
    client = redis.ext.client
    client.set('test_key1', 10)
    assert redis.dict == {b'test_key1': b'10'}


def test_get(redis):
    client = redis.ext.client
    client.set('test_key1', 10)
    result = client.get('test_key1')
    assert result == b'10'


def test_get_wrongtype(redis):
    client = redis.ext.client
    client.sadd('test', 1)

    with pytest.raises(ResponseError, match='WRONGTYPE'):
        client.get('test')
    assert redis.dict == {b'test': {b'1'}}


def test_set_wrongtype(redis):
    client = redis.ext.client
    client.sadd('test', 1)
    assert redis.dict == {b'test': {b'1'}}
    client.set('test', 2)
    assert redis.dict == {b'test': b'2'}


def test_get_unexistent(redis):
    client = redis.ext.client
    assert client.get('test') is None


def test_incrby(redis):
    client = redis.ext.client
    client.set('test', 1)
    assert client.incrby('test', 2) == 3
    assert redis.dict == {b'test': b'3'}


def test_incrby_wrongtype(redis):
    client = redis.ext.client
    client.sadd('test', 1)
    with pytest.raises(ResponseError, match='WRONGTYPE'):
        client.incrby('test', 2)
    assert redis.dict == {b'test': {b'1'}}


def test_incrby_notint_key(redis):
    client = redis.ext.client
    client.set('test', 'value')
    with pytest.raises(ResponseError, match='value is not an integer'):
        client.incrby('test', 2)
    assert redis.dict == {b'test': b'value'}


def test_incrby_notint_value(redis):
    client = redis.ext.client
    client.set('test', 1)
    with pytest.raises(ResponseError, match='value is not an integer'):
        client.incrby('test', 'value')
    assert redis.dict == {b'test': b'1'}


def test_decrby(redis):
    client = redis.ext.client
    client.set('test', 3)
    assert client.execute_command('DECRBY', 'test', 2) == 1
    assert redis.dict == {b'test': b'1'}


def test_decrby_wrongtype(redis):
    client = redis.ext.client
    client.sadd('test', 3)
    with pytest.raises(ResponseError, match='WRONGTYPE'):
        client.execute_command('DECRBY', 'test', 2)
    assert redis.dict == {b'test': {b'3'}}


def test_decrby_notint_key(redis):
    client = redis.ext.client
    client.set('test', 'value')
    with pytest.raises(ResponseError, match='value is not an integer'):
        client.execute_command('DECRBY', 'test', 2)
    assert redis.dict == {b'test': b'value'}


def test_decrby_notint_value(redis):
    client = redis.ext.client
    client.set('test', 1)
    with pytest.raises(ResponseError, match='value is not an integer'):
        client.execute_command('DECRBY', 'test', 'value')
    assert redis.dict == {b'test': b'1'}
