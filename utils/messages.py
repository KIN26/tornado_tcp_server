from functools import reduce


async def parse_inbox_msg(msg):

    header = await msg.read_bytes(1)
    message_id = await msg.read_bytes(2)
    source_id = await msg.read_bytes(8)
    status = await msg.read_bytes(1)
    filed_count = await msg.read_bytes(1)
    filed_count_int = int.from_bytes(
        filed_count,
        byteorder='big',
        signed=False
    )
    fields_b = await msg.read_bytes(12 * filed_count_int)
    fields = await _get_inbox_msg_fields(filed_count_int, fields_b)
    source_xor = await msg.read_bytes(1)

    _validate_inbox_xor(source_xor, (
        header
        + message_id
        + source_id
        + status
        + filed_count
        + fields_b
    ))

    msg = {
        'header': header,
        'message_id': int.from_bytes(
            message_id,
            byteorder='big',
            signed=False
        ),
        'id': source_id.decode('ascii', 'ignore'),
        'status': status,
        'fields': fields,
    }

    return msg


async def get_outbox_msg(header, message_id):
    message_id = int.to_bytes(
        message_id,
        2,
        byteorder='big',
        signed=False
    )
    out = bytes(header + message_id)
    return out + _get_xor(out)


async def _get_inbox_msg_fields(filed_count, fields_byte_str):
    data = []
    i = 0
    while filed_count > i:
        byte_index = i * 12
        field_name = fields_byte_str[byte_index:byte_index+8].decode(
            'ascii',
            'ignore'
        )
        field_value = int.from_bytes(
            fields_byte_str[byte_index+8:byte_index+12],
            byteorder='big',
            signed=False
        )
        data.append([field_name, field_value])
        i += 1
    return data


def _get_xor(byte_obj):
    a, *b = byte_obj
    return bytes([reduce(lambda x, y: x ^ y, b, a)])


def _validate_inbox_xor(source_xor, msg_bytes_str):
    if source_xor != _get_xor(msg_bytes_str):
        raise ValueError('Invalid inbox xor')
