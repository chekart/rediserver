from . import resp


class CommandQueue:
    """
    A simple abstraction to support transactions
    """

    def __init__(self, redis_server):
        self.redis = redis_server
        self.transaction = None
        self.watch = set()
        self.rollback = False

    def reset(self):
        self.transaction = None
        self.rollback = False
        self.watch.clear()
        self.redis.remove_watch(self)

    def on_change(self, key):
        if key in self.watch:
            self.rollback = True

    def execute(self, command, *command_args):
        if command == b'UNWATCH':
            self.watch.clear()
            self.redis.remove_watch(self)
            return resp.OK

        if self.transaction is None:
            return self.execute_without_transaction(command, *command_args)
        return self.execute_with_transaction(command, *command_args)

    def execute_with_transaction(self, command, *args):
        assert self.transaction is not None

        if command == b'MULTI':
            raise NotImplementedError()
        if command == b'EXEC':
            to_execute = self.transaction
            rollback = self.rollback
            self.reset()

            if rollback:
                return resp.NIL

            result = []
            for current_command, current_args in to_execute:
                result.append(
                    self.redis.execute_single(current_command, *current_args)
                )
            return result

        self.transaction.append((command, args))
        return resp.QUEUED

    def execute_without_transaction(self, command, *args):
        assert self.transaction is None

        if command == b'MULTI':
            # start transaction
            self.transaction = []
            return resp.OK
        if command == b'WATCH':
            self.watch.add(args[0])
            self.redis.add_watch(self)
            return resp.OK

        return self.redis.execute_single(command, *args)
