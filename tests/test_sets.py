import pytest
from redis.exceptions import ResponseError


def test_add(redis):
    client = redis.ext.client
    assert client.sadd('test_key1', 10) == 1
    assert redis.dict == {b'test_key1': {b'10'}}


def test_add_multiple(redis):
    client = redis.ext.client
    assert client.sadd('test_key1', 10, 11) == 2
    assert redis.dict == {b'test_key1': {b'10', b'11'}}


def test_add_existing(redis):
    client = redis.ext.client
    client.sadd('test_key1', 10, 11)
    assert client.sadd('test_key1', 10, 11, 12) == 1
    assert redis.dict == {b'test_key1': {b'10', b'11', b'12'}}


def test_add_wrongtype(redis):
    client = redis.ext.client
    client.set('test_key1', 1)

    with pytest.raises(ResponseError, match='WRONGTYPE'):
        client.sadd('test_key1', 2)

    assert redis.dict == {b'test_key1': b'1'}
    assert client.get('test_key1') == b'1'


def test_pop(redis):
    client = redis.ext.client
    client.sadd('test_key1', 10, 20)
    result = client.spop('test_key1')
    assert result in (b'10', b'20')
    assert redis.dict == {b'test_key1': {b'10', b'20'} - {result}}


def test_pop_to_none(redis):
    client = redis.ext.client
    client.sadd('test_key1', 20)
    client.spop('test_key1')
    assert redis.dict == {}


def test_pop_wrongtype(redis):
    client = redis.ext.client
    client.set('test_key1', 1)

    with pytest.raises(ResponseError, match='WRONGTYPE'):
        client.spop('test_key1')

    assert redis.dict == {b'test_key1': b'1'}
    assert client.get('test_key1') == b'1'


def test_pop_empty(redis):
    client = redis.ext.client
    result = client.spop('test_key1')
    assert result is None
    assert redis.dict == {}


def test_scard(redis):
    client = redis.ext.client
    client.sadd('test', 1)
    assert client.scard('test') == 1