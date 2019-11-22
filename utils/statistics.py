from time import time


class Statistics:

    statuses = {b"\x01": "IDLE", b"\x02": "ACTIVE", b"\x03": "RECHARGE"}

    def __init__(self):
        self.data = dict()

    def set(self, source_hash, source):
        self.data[source_hash] = dict({
            'id': source['id'],
            'last_message_id': source['message_id'],
            'status': self.statuses[source['status']],
            'ts': int(time())
        })

    def remove(self, source_hash):
        if source_hash in self.data:
            del self.data[source_hash]
