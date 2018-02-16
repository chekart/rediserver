import inspect
import hashlib

from lupa import LuaRuntime

from . import resp


class KeyType:
    def __init__(self, type_):
        self.type_ = type_


MUTABLE_KEY = object()
KEY_SET = KeyType(set)
KEY_STRING = KeyType(bytes)


def redis_command(command):
    def wrapper(func):
        info = inspect.getfullargspec(func)

        mutable_keys = []
        key_types = {}
        for arg, annotation in info.annotations.items():
            if not isinstance(annotation, tuple):
                annotation = (annotation,)

            for prop in annotation:
                if prop is MUTABLE_KEY:
                    mutable_keys.append(arg)
                if isinstance(prop, KeyType):
                    key_types[arg] = prop.type_

        def new_func(self, *args, **kwargs):
            values = {}
            values.update(kwargs)
            for index, arg_value in enumerate(args, start=1):
                if index >= len(info.args):
                    # varargs
                    break
                values[info.args[index]] = arg_value

            for key in mutable_keys:
                self.on_change(values[key])

            for key, key_type in key_types.items():
                self.assert_key_type(values[key], key_type)

            return func(self, *args, **kwargs)

        new_func.redis_command = command
        return new_func
    return wrapper


class Redis:
    def __init__(self):
        self.keys = {}
        self.scripts = {}
        self.watches = set()
        self.execute_map = {}
        self.cursors = {}

        self.lua_proxy = self.get_lua_proxy()
        self.lua = LuaRuntime(
            encoding=None,
            unpack_returned_tuples=True
        )

        for _, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(func, 'redis_command'):
                self.execute_map[func.redis_command] = func

    def get_lua_proxy(self):
        redis = self

        class RedisProxy:
            def call(self, command, *args):
                return redis.execute_single(command, *args)

            def replicate_commands(self):
                pass

        return RedisProxy()

    def add_watch(self, queue):
        self.watches.add(queue)

    def remove_watch(self, queue):
        if queue in self.watches:
            self.watches.remove(queue)

    def on_change(self, key):
        for queue in self.watches:
            queue.on_change(key)

    def execute_single(self, command, *args):
        try:
            return self.execute_map[command.decode().upper()](*args)
        except KeyError:
            raise resp.Error('ERR', 'Command {} is not implemented yet'.format(command))

    @redis_command('SET')
    def execute_set(self, key: MUTABLE_KEY, value):
        self.keys[key] = value
        return resp.OK

    @redis_command('GET')
    def execute_get(self, key: KEY_STRING):
        if key not in self.keys:
            return resp.NIL
        return self.keys[key]

    @redis_command('INCRBY')
    def execute_incrby(self, key: (MUTABLE_KEY, KEY_STRING), value):
        try:
            initial = int(self.keys.get(key, 0))
            value = int(value)
        except ValueError:
            raise resp.Errors.NOT_INT

        result = initial + value
        self.keys[key] = str(result).encode()
        return result

    @redis_command('DECRBY')
    def execute_decrby(self, key: (MUTABLE_KEY, KEY_STRING), value):
        try:
            initial = int(self.keys.get(key, 0))
            value = int(value)
        except ValueError:
            raise resp.Errors.NOT_INT

        result = initial - value
        self.keys[key] = str(result).encode()
        return result

    @redis_command('DEL')
    def execute_del(self, *keys):
        for key in keys:
            if key in self.keys:
                self.on_change(key)
                del self.keys[key]
        return resp.OK

    @redis_command('SCAN')
    def execute_scan(self, cursor):
        try:
            cursor = int(cursor)
        except ValueError:
            return resp.Errors.INVALID_CURSOR

        if cursor == 0:
            cursor = max(self.cursors.keys()) if self.cursors else 1
            self.cursors[cursor] = iter(set(self.keys.keys()))

        bulk = []
        for item in self.cursors[cursor]:
            bulk.append(item)
            if len(bulk) > 5:
                break
        else:
            del self.cursors[cursor]
            cursor = 0

        return [cursor, bulk]

    @redis_command('SADD')
    def execute_sadd(self, key: (MUTABLE_KEY, KEY_SET), *args):
        if key not in self.keys:
            self.keys[key] = set()

        values = self.keys[key]
        to_add = set(args) - values
        values.update(to_add)
        return len(to_add)

    @redis_command('SPOP')
    def execute_spop(self, key: (MUTABLE_KEY, KEY_SET)):
        if key not in self.keys:
            return resp.NIL
        values = self.keys[key]
        result = values.pop()

        if not values:
            del self.keys[key]

        return result

    @redis_command('SCARD')
    def execute_scard(self, key: KEY_SET):
        if key not in self.keys:
            return 0
        return len(self.keys[key])

    @redis_command('EVALSHA')
    def execute_evalsha(self, script_sha, *args):
        if script_sha not in self.scripts:
            return resp.Error('NOSCRIPT')

        num_keys, *script_args = args
        num_keys = int(num_keys)

        keys = script_args[:num_keys]
        vals = script_args[num_keys:]

        func = self.scripts[script_sha]
        result = func(self.lua_proxy, self.lua.table(*keys), self.lua.table(*vals))

        return result

    @redis_command('SCRIPT')
    def execute_script_load(self, action, script):
        if action == b'LOAD':
            sha = hashlib.sha1(script).hexdigest().encode()
            lua_func = 'function(redis, KEYS, ARGV) {} end'.format(script.decode())
            self.scripts[sha] = self.lua.eval(lua_func)
            return sha

        raise NotImplementedError()

    def assert_key_type(self, key, type_):
        if key not in self.keys:
            return

        if not isinstance(self.keys[key], type_):
            raise resp.Errors.WRONGTYPE
