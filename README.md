# Task Description

It is needed to develop application on tornado framework. The application should listen to two ports (8888 and 8889).
On the first port application should get connections and messages from connected clients ("sources").

The structure of source's message:
 - 1 byte - header (always 0x01)
 - 2 bytes - message number within current connection (int type)
 - 8 bytes - source id (ascii string)
 - 1 byte - source status (int type), possible value: 0x01 - IDLE, 0x02 - ACTIVE, 0x03 - RECHARGE
 - 1 byte - numfields - Count of data fields (int type)
 - According to count of fields value there are several pairs of fields of the following type:
    - 8 bytes - field name (ascii string)
    - 4 bytes - field value (int type)
 - 1 byte - XOR bytes sum
 
The application server sends the following messages in response::

- 1 byte - header. If the message is processed successfully then - 0x11, otherwise 0x12
- 2 bytes - message number or 0x00 if message is processed unsuccessfully
- 1 byte - bitwise XOR from message

To all clients connected to 8889 port ("listeners"), for each message received from the source the application must send messages in the following text format:

    [source id] <field name> | <field value> \r\n
    
One line for each pair name-value.

When a new listener is connected to 8889 port, application should send to him a list of all currently connected sources in the following format:

        [source_id] <number of the last message> | <status (string "IDLE", "ACTIVE" or "RECHARGE"> | <last message timestamp> \r\n
        
 One line for each source.

# Used technologies
- tornado