import redis
from rediserver.test import local_redis


LUA_GETMOVE = """
redis.replicate_commands()
local v = redis.call("GET", KEYS[1])
if v then
    redis.call("SET", KEYS[2], v)
end
return v
"""

with local_redis() as redis_server:
    client = redis.StrictRedis(unix_socket_path=redis_server.sock)

    client.set('key1', 3)
    print(client.get('key1'))

    getmove = client.register_script(LUA_GETMOVE)
    result = getmove(keys=['key1', 'key2'])
    print(result)

    print(redis_server['key1'])
    print(redis_server['key2'])
