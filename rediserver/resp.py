SYM_CRLF = b'\r\n'
OK = object()
QUEUED = object()
NIL = None


class Error(Exception):
    def __init__(self, class_, msg=''):
        self.class_ = class_
        self.message = msg


class Errors:
    INVALID_CURSOR = Error('ERR', 'invalid cursor')
    NOT_INT = Error('ERR', 'value is not an integer or out of range')
    WRONGTYPE = Error('WRONGTYPE', 'Operation against a key holding the wrong kind of value')


async def read_command(reader):
    data = await reader.readuntil(SYM_CRLF)

    type_ = chr(data[0])
    data = data[1:-len(SYM_CRLF)]

    if type_ == ':':
        return float(data)
    if type_ == '$':
        length = int(data)
        if length == -1:
            return None
        string = await reader.readexactly(length)
        await reader.readexactly(len(SYM_CRLF))
        return string
    if type_ == '*':
        length = int(data)
        return [
            await read_command(reader) for _ in range(length)
        ]

    raise NotImplementedError('Unknown message type: {}'.format(type_))


def _resp_dumps(value):
    if value is OK:
        return [b'+OK']

    if value is NIL:
        return [b'$-1']

    if value is QUEUED:
        return [b'+QUEUED']

    if isinstance(value, int):
        return [b':' + str(value).encode()]

    if isinstance(value, str):
        value = value.encode()

    if isinstance(value, bytes):
        return [b'$' + str(len(value)).encode(), value]

    if isinstance(value, Error):
        return [b'-' + str(value.class_).encode() + b' ' + str(value.message).encode()]

    if isinstance(value, (list, tuple)):
        result = [b'*' + str(len(value)).encode()]
        for item in value:
            result.extend(_resp_dumps(item))
        return result

    raise NotImplementedError()


def dump_response(value):
    response = _resp_dumps(value)
    response = SYM_CRLF.join(response) + SYM_CRLF
    return response
