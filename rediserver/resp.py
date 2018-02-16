SYM_CRLF = b'\r\n'
OK_REPLY = b'+OK' + SYM_CRLF
NIL_REPLY = b'$-1\r\n'
QUEUED_REPLY = b'+QUEUED' + SYM_CRLF
NOT_SUPPORTED_REPLY = b'-ERR command is not supported\r\n'
OK = object()
QUEUED = object()
NIL = None


class Error(Exception):
    def __init__(self, class_, msg=''):
        self.class_ = class_
        self.message = msg


class Errors:
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
    if isinstance(value, int):
        return [b':' + str(value).encode()]

    if isinstance(value, str):
        value = value.encode()

    if isinstance(value, bytes):
        return [b'$' + str(len(value)).encode(), value]

    if isinstance(value, Error):
        return [b'-' + str(value.class_).encode() + b' ' + str(value.message).encode()]

    raise NotImplementedError()


def dump_response(value):
    if value is OK:
        response = OK_REPLY
    elif value is None or value is NIL:
        response = NIL_REPLY
    elif value is QUEUED:
        response = QUEUED_REPLY
    else:
        response = _resp_dumps(value)
        response = SYM_CRLF.join(response) + SYM_CRLF

    return response
