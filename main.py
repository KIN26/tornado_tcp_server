from tornado.ioloop import IOLoop
from server import TornadoTCPServer
from handlers import source, listener
from utils import statistics
import settings


if __name__ == '__main__':

    sources_statistics = statistics.Statistics()
    listeners = set()

    source_server = TornadoTCPServer(
        sources_statistics,
        listeners,
        source.SourceHandler
    )
    source_server.listen(settings.PORTS['source'])

    listener_server = TornadoTCPServer(
        sources_statistics,
        listeners,
        listener.ListenerHandler
    )
    listener_server.listen(settings.PORTS['listener'])

    IOLoop.current().start()
