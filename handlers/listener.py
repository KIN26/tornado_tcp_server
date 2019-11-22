class ListenerHandler:

    def __init__(self, statistics, listeners):
        self.statistics = statistics
        self.listeners = listeners

    async def run(self, stream):
        await self._send_statistics(stream)
        await self._add_listener_to_storage(stream)
        await stream.read_until_close()
        await self._remove_listener_from_storage(stream)

    async def _add_listener_to_storage(self, stream):
        self.listeners.add((
            hash(stream),
            stream
        ))

    async def _remove_listener_from_storage(self, stream):
        self.listeners.remove((
            hash(stream),
            stream
        ))

    async def _send_statistics(self, stream):
        for item in self.statistics.data.values():
            stat_str = '[{0}] {1} | {2} | {3}\r\n'
            stat_str = stat_str.format(
                item['id'],
                item['last_message_id'],
                item['status'],
                item['ts']
            )
            await stream.write(stat_str.encode('ascii'))
