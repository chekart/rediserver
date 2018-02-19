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
with local_redis() as redis_proxy:
    # redis_proxy contains sock property a tempfile path to redis unix socket
    # pass it to python redis client
    client = redis.StrictRedis(unix_socket_path=redis_proxy.sock)
    client.set('key1', 1)
    # dict property returns a deepcopy of redis keys, feel free to modify it
    # and check whether data is created
    # please note that data stored as bytes
    assert redis_proxy.dict == {b'key1': b'1'}
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
  * GET, SET, DEL, INCRBY, DECRBY, SCAN
* Sets
  * SADD, SPOP, SCARD
* Scripts
  * SCRIPT LOAD, EVALSHA
* Transactions:
  * MULTI, WATCH, EXEC

## Embedded Redis

Need a real redis instance to be flushed for each test? Say no more.
You can use `EmbeddedRedis` and `EmbeddedRedisSession` context managers

EmbeddedRedis context manager runs a docker redis container on enter and
stops it on exit. The return value of the container is a temporary socket file
to use for connecting server. It's also possible to use start and stop methods of
EmbeddedRedis directly

```python
import redis
from rediserver import EmbeddedRedis

with EmbeddedRedis() as socket_file:
    client = redis.StrictRedis(unix_socket_path=embedded_redis_server)
    client.set('some_key', 'some_value')
```

EmbeddedRedisSession is a context manager that flushes current redis db on exit
In case of multithreaded testing, each thread has to run session using separate db
(the current redis db limit if using EmbeddedRedis is set to 100). Returned value is
a redis proxy object similar to `local_redis`

```python
redis_server = EmbeddedRedis()
socket = redis_server.start()

client = redis.StrictRedis(unix_socket_path=redis_proxy.sock, db=thread_db)

with EmbeddedRedisSession(socket_file=socket, db=thread_db) as redis_proxy:
    client.set('some_key', 'some_value')

client.get('some_key') # value is None
redis_server.stop()
```

### pytest

The package provides the following pytest fixtures to use.

embedded_redis_server - creates redis server instance, with the scope of session

embedded_redis - flushes redis db before and after the test
