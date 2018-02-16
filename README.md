[![Build Status](https://travis-ci.org/chekart/rediserver.svg?branch=dev)](https://travis-ci.org/chekart/rediserver)

# rediserver

Pure Python Redis server implementation

## Getting Started

It is possible to use Redis server as standalone redis installation,
however the main goal of the project is to have an in-mem lightweight Redis for python Unit Tests.

The package provides context manager named local_redis which created separate thread running fresh new redis on enter
and stops on exit. Context manager returns proxy object to access redis data

```python
import redis
from rediserver.test import local_redis

# start redis server
with local_redis() as redis_mock:
    # redis_mock contains sock property a tempfile path to redis unix socket
    # pass it to python redis client
    client = redis.StrictRedis(unix_socket_path=redis_mock.sock)
    client.set('key1', 1)
    # dict property returns a deepcopy of redis keys, feel free to modify it
    # and check whether data is created
    # please note that data stored as bytes
    assert redis_mock.dict == {b'key1': b'1'}
```

### pytest

The package provides pytest fixture, use it like this

```python
# in conftest.py
pytest_plugins = 'rediserver.test.pytest',

def test_ok(local_redis):
    client = redis.StrictRedis(unix_socket_path=local_redis.sock)
    ...
```

## Compatibility

Currently redis server supports the following methods:

* Keys
..* GET, SET, DEL, INCRBY, DECRBY, SCAN
* Sets
..* SADD, SPOP, SCARD
* Scripts
..* SCRIPT LOAD, EVALSHA
* Transactions:
..* MULTI, WATCH, EXEC