# nmeaserver
Python framework for a NMEA 0183 TCP Server inspired by Flask developer API

Create your first NMEA Server
------------------
The nmeaserver framework is inspired from the Flask interface to make it straight-forward to setup server.

To create your first server, all you need to do is:
```python
from nmea import server, formatter

# Creates a nmeaserver
nmeaserver = server.NMEAServer()

# Create a message handler that receives all messages with the sentence ID: 'RXTST'
@nmeaserver.message('RXTST')
def tst_handler(self, context, message):
    return formatter.format('TXTST,Message Received!')

# Starts the server
nmeaserver.start()
```