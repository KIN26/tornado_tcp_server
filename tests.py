import socket

from tornado.testing import AsyncTestCase, bind_unused_port, gen_test
from tornado.iostream import IOStream
from tornado import gen
from server import TornadoTCPServer
from handlers import source, listener
from utils.statistics import Statistics
from utils.messages import _get_xor


class TornadoTPCServerTestCase(AsyncTestCase):

    def setUp(self):
        super().setUp()

        listeners = set()
        statistics = Statistics()

        self.source_server_clients = []
        self.listener_server_clients = []

        self.source_server = TornadoTCPServer(statistics, listeners, source.SourceHandler)
        sock, self.source_server_port = bind_unused_port()
        self.source_server.add_socket(sock)

        self.listener_server = TornadoTCPServer(statistics, listeners, listener.ListenerHandler)
        sock, self.listener_server_port = bind_unused_port()
        self.listener_server.add_socket(sock)

        self.source_client_msg_one = bytes(
            b'\x01'
            + int.to_bytes(1, 2, byteorder='big', signed=False)
            + 'abcdefgh'.encode()
            + b'\x01'
            + int.to_bytes(1, 1, byteorder='big', signed=False)
            + 'foofield'.encode()
            + int.to_bytes(1, 4, byteorder='big', signed=False)
        )
        self.source_client_msg_one += _get_xor(self.source_client_msg_one)

        self.source_client_msg_two = bytes(
            b'\x01'
            + int.to_bytes(1, 2, byteorder='big', signed=False)
            + 'ijklmnop'.encode()
            + b'\x01'
            + int.to_bytes(1, 1, byteorder='big', signed=False)
            + 'fieldfoo'.encode()
            + int.to_bytes(2, 4, byteorder='big', signed=False)
        )
        self.source_client_msg_two += _get_xor(self.source_client_msg_two)

        self.source_client_invalid_msg = bytes(
            b'\x01'
            + int.to_bytes(10, 2, byteorder='big', signed=False)
            + 'ijklmnop'.encode()
            + b'\x01'
            + int.to_bytes(1, 1, byteorder='big', signed=False)
            + 'fieldfoo'.encode()
            + int.to_bytes(2, 4, byteorder='big', signed=False)
            + int.to_bytes(1, 1, byteorder='big', signed=False)
        )

    @gen_test
    def test_source_client_msg(self):
        client = yield self.connect_client_to_server(self.source_server_port, self.source_server_clients)
        yield client.write(self.source_client_msg_one)
        response = yield client.read_bytes(4)
        self.close_server_connection(self.source_server, self.source_server_clients)
        self.assertEqual(response, bytes(
            b'\x11'
            + int.to_bytes(1, 2, byteorder='big', signed=False)
            + _get_xor(bytes(
                b'\x11'
                + int.to_bytes(1, 2, byteorder='big', signed=False)
            ))
        ))


    @gen_test
    def test_source_client_invalid_message(self):
        client = yield self.connect_client_to_server(self.source_server_port, self.source_server_clients)
        yield client.write(self.source_client_invalid_msg)
        response = yield client.read_bytes(4)
        self.close_server_connection(self.source_server, self.source_server_clients)
        self.assertEqual(response, bytes(
            b'\x12'
            + int.to_bytes(0, 2, byteorder='big', signed=False)
            + _get_xor(bytes(
                b'\x12'
                + int.to_bytes(0, 2, byteorder='big', signed=False)
            ))
        ))

    @gen_test
    def test_listener_statistics(self):
        source_client = yield self.connect_client_to_server(self.source_server_port, self.source_server_clients)
        yield source_client.write(self.source_client_msg_one)
        yield gen.sleep(2)

        listener_client = yield self.connect_client_to_server(self.listener_server_port, self.listener_server_clients)
        response = yield listener_client.read_until('\r\n'.encode('ascii'))

        self.close_server_connection(self.listener_server, self.listener_server_clients)
        self.close_server_connection(self.source_server, self.source_server_clients)

        self.assertTrue(str(response).find('[abcdefgh] 1 | IDLE |') >= 0)

    @gen_test
    def test_listener_multiplie_statistics(self):
        source_client_one = yield self.connect_client_to_server(self.source_server_port, self.source_server_clients)
        yield source_client_one.write(self.source_client_msg_one)

        source_client_two = yield self.connect_client_to_server(self.source_server_port, self.source_server_clients)
        yield source_client_two.write(self.source_client_msg_two)

        yield gen.sleep(2)

        listener_client = yield self.connect_client_to_server(self.listener_server_port, self.listener_server_clients)
        response = ''
        for i in range(2):
            tmp_response = yield listener_client.read_until('\r\n'.encode('ascii'))
            response += str(tmp_response)

        self.close_server_connection(self.listener_server, self.listener_server_clients)
        self.close_server_connection(self.source_server, self.source_server_clients)

        self.assertTrue((
            str(response).find('[abcdefgh] 1 | IDLE |') >= 0
            and str(response).find('[ijklmnop] 1 | IDLE |') >= 0
        ))

    @gen_test
    def test_delivery_message_from_source_to_listener(self):
        source_client = yield self.connect_client_to_server(self.source_server_port, self.source_server_clients)
        listener_client = yield self.connect_client_to_server(self.listener_server_port, self.listener_server_clients)

        yield source_client.write(self.source_client_msg_one)

        yield gen.sleep(2)

        response = yield listener_client.read_until('\r\n'.encode('ascii'))

        self.close_server_connection(self.listener_server, self.listener_server_clients)
        self.close_server_connection(self.source_server, self.source_server_clients)

        self.assertEqual(response, b'[abcdefgh] foofield | 1\r\n')

    async def connect_client_to_server(self, server_port, clients_storage):
        client = IOStream(socket.socket())
        await client.connect(('localhost', server_port))
        clients_storage.append(client)
        return client

    def close_server_connection(self, server, server_clients):
        for client in server_clients:
            client.close()
        server.stop()
