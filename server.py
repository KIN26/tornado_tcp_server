from tornado.tcpserver import TCPServer


class TornadoTCPServer(TCPServer):

    def __init__(self, sources, listeners, handler, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler(sources, listeners)

    async def handle_stream(self, stream, address):
        await self.handler.run(stream)
