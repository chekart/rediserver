import asyncio
import asyncio.streams

from threading import Thread, Event

from . import resp
from .redis import Redis
from .queue import CommandQueue


def create_redis_server():
    redis_server = Redis()

    async def on_connect(reader, writer):
        transaction = CommandQueue(redis_server)

        try:
            while True:
                command, *command_args = await resp.read_command(reader)
                try:
                    result = transaction.execute(command, *command_args)
                except resp.Error as e:
                    response = resp.dump_response(e)
                    transaction.reset()
                except Exception as e:
                    response = resp.dump_response(
                        resp.Error('UNKNOWN', str(e))
                    )
                    transaction.reset()
                else:
                    response = resp.dump_response(result)

                writer.write(response)
                await writer.drain()
        except asyncio.streams.IncompleteReadError:
            writer.close()

    return redis_server, on_connect


def run_tcp(host='127.0.0.1', port=6379):
    run(endpoint=(host, port))


def run_sock(path):
    run(unix_domain_socket=path)


def _create(endpoint=None, unix_domain_socket=None):
    assert (unix_domain_socket is None) != (endpoint is None)

    loop = asyncio.new_event_loop()
    redis_instance, on_connect = create_redis_server()

    if unix_domain_socket:
        socket_server = asyncio.start_unix_server(on_connect, path=unix_domain_socket, loop=loop)
    else:
        host, port = endpoint
        socket_server = asyncio.start_server(on_connect, host=host, port=port, loop=loop)

    return redis_instance, loop, socket_server


def _run_forever(loop, socket_server, started_event=None):
    server = loop.run_until_complete(socket_server)

    if started_event:
        started_event.set()

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


def run(endpoint=None, unix_domain_socket=None):
    redis_instance, loop, socket_server = _create(endpoint=endpoint, unix_domain_socket=unix_domain_socket)
    _run_forever(loop, socket_server)


def run_threaded(unix_domain_socket):
    started_event = Event()

    class Data:
        def __init__(self):
            self.redis_instance = None
            self.loop = None

    data = Data()

    def thread_target():
        data.redis_instance, data.loop, socket_server = _create(unix_domain_socket=unix_domain_socket)
        _run_forever(data.loop, socket_server, started_event)

    thread = Thread(target=thread_target)
    thread.start()
    started_event.wait()

    def shutdown():
        for task in asyncio.Task.all_tasks():
            task.cancel()
        data.loop.stop()

    def shutdown_callback():
        data.loop.call_soon_threadsafe(shutdown)

    return data.redis_instance, thread, shutdown_callback
