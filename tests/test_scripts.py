import pytest
from redis.exceptions import ResponseError


SPOPMOVE = """
redis.replicate_commands()
local v = redis.call("SPOP", KEYS[1])
if v then
    redis.call("SADD", KEYS[2], v)
end
return v
"""


def test_create_script(redis):
    client = redis.ext.client
    fn = client.register_script(SPOPMOVE)
    client.sadd('test1', 1, 2)
    client.sadd('test2', 3)
    result = fn(keys=['test1', 'test2'])
    assert result in (b'1', b'2')
    assert redis.dict == {b'test1': {b'1', b'2'} - {result}, b'test2': {b'3'} | {result}}
