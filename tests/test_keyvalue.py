import pytest
from redis.exceptions import ResponseError


KEYS_DATA = {
    b'key1': 1,
    b'key3': 5,
    b'some_key': 7,
    b'a_key': 'value',
    b'the_key': '0',
    b'test': 10,
    b'data': 11,
}


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


def test_scan(redis):
    client = redis.ext.client
    for key, value in KEYS_DATA.items():
        client.set(key, value)

    result = {item for item in client.scan_iter()}
    assert result == set(KEYS_DATA.keys())


def test_scan_wrong_value(redis):
    client = redis.ext.client
    with pytest.raises(ResponseError, match='invalid cursor'):
        client.scan('value')


def test_scan_add(redis):
    client = redis.ext.client
    for key, value in KEYS_DATA.items():
        client.set(key, value)

    added = False
    result = set()

    cursor = '0'
    while cursor != 0:
        cursor, data = client.scan(cursor=cursor)
        for item in data:
            result.add(item)
        added = True
        client.set('another_key', 1)

    assert added
    assert result == set(KEYS_DATA.keys())
