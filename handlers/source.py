from tornado.iostream import StreamClosedError
from utils import messages
from consts import SOURCE_RESPONSE_FAIL, SOURCE_RESPONSE_SUCCESS


class SourceHandler:

    def __init__(self, statistics, listeners):
        self.statistics = statistics
        self.listeners = listeners

    async def run(self, stream):
        while True:
            try:
                try:
                    message = await messages.parse_inbox_msg(stream)
                    self.statistics.set(hash(stream), message)
                    await self._send_fields_to_listeners(message)
                except BaseException:
                    outbox_msg = await messages.get_outbox_msg(
                        SOURCE_RESPONSE_FAIL,
                        0
                    )
                else:
                    outbox_msg = await messages.get_outbox_msg(
                        SOURCE_RESPONSE_SUCCESS,
                        message['message_id']
                    )
                await stream.write(outbox_msg)
            except StreamClosedError:
                self.statistics.remove(hash(stream))
                break

    async def _send_fields_to_listeners(self, message):
        for listener_hash, listener_stream in self.listeners:
            notify_pattern = '[{0}] {1} | {2}'
            fields_str = '\r\n'.join([notify_pattern.format(
                message['id'],
                field[0],
                field[1]
            ) for field in message['fields']])
            fields_str += '\r\n'
            await listener_stream.write(fields_str.encode('ascii'))
