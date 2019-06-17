import threading
import SocketServer
import formatter
import logging
import signal
import select
import time

logger = logging.getLogger("nmeaserver")
signal.signal(signal.SIGINT, signal.SIG_DFL)

class NMEAServer:
    def default_error_handler(self, context, err):
        logger.debug("Error detected in default nmeaserver handler", 
                     kwargs={"exc_info": 1})
        return formatter.format(self.error_sentence_id + 
                                ", The nmeaserver experienced an exception." \
                                " Check the debug logs")

    def default_bad_checksum(self, context, raw_message):
        good_checksum = formatter.calc_checksum(raw_message)
        err_msg = "Message '{}' has a bad checksum. Correct checksum is '{}'" \
            .format(raw_message, good_checksum)
        logger.debug(err_msg)
        return formatter.format(self.error_sentence_id + "," + err_msg)


    def default_missing_handler(self, context, message):
        valid_ids = ", ".join(self.message_handlers.keys())
        err_msg = "Received message '{}' but the  valid messageIds are: '{}'" \
            .format(message['sentence_id'], valid_ids)
        logger.debug(err_msg)
        return formatter.format(self.error_sentence_id + "," + err_msg)

    #: The dictionary of handler functions for well-formed nmea messages.
    #: .. versionadded:: 1.0
    message_handlers = {}

    #: The handler to be called when a message with an unknown messageId is
    #: received.
    #: .. versionadded:: 1.0
    missing_handler = default_missing_handler

    #: An optional handler that when defined is called prior to any message
    #: handler function.
    #: .. versionadded:: 1.0
    message_pre_handler = None

    #: An optional handler that when defined is called after any message
    #: handler function.
    #: .. versionadded:: 1.0
    message_post_handler = None

    #: An optional handler that when defined is called when an error occurs.
    #: .. versionadded:: 1.0
    error_handler = default_error_handler

    #: An optional handler that when defined is called when a message without a
    #: checksum or with an invalid checksum is received.
    #: .. versionadded:: 1.0
    bad_checksum_message_handler = default_bad_checksum

    #: An optional function that creates a connection-scoped dictionary that
    # represents the 'context' of that connection.
    #: .. versionadded:: 1.0
    connection_context_creator = None

    #: An optional function to be called when a new connection is created that
    #: can stream responses without the need for a request. Note that this
    #: functional will be called by a new thread different from the listener.
    #: .. versionadded:: 0.1.8
    response_streamer = None

    #: The host to start this NMEAServer on.
    host = None

    #: The port to start this NMEAServer on.
    port = None

    #: Whether the NMEAServer is to be run in debug mode.
    debug = False

    #: Whether this NMEAServer is being shutdown.
    shutdown_flag = False

    #: The thread instance running this server
    server_thread = None
    
    error_sentence_id = 'TXERR'

    def __init__(self, host='', 
                 port=9000, 
                 debug=False, 
                 error_sentence_id='TXERR'):
        self.host = host
        self.port = port
        self.debug = debug
        self.error_sentence_id = error_sentence_id

    def message(self, message_id):
        """A decorator that registers a function for handling a given message
        ID. Functionally identical to :meth:`add_message_handler` but offering
        a decorator wrapper::

            @NMEAServer.message('RBHRB')
            def HRB(context, message):
                return nmea.format("$TXHRB,Success")

        :param message_id: the ID as string of the message to handle
        """

        def decorator(f):
            self.add_message_handler(message_id, f)
            return f
        return decorator

    def add_message_handler(self, message_id, handler_func=None):
        """Connects a handler function to a message_id.  Functionally identical
        to :meth:`message` decorator.  If a handler_func is provided it will be
        registered for the message_id.

        For example::

            @NMEAServer.message('RBHRB')
            def HRB(context, message):
                return nmea.format("$TXHRB,Success")

        Is the same as::

            def HRB(context, message):
                return nmea.format("$TXHRB,Success")
            app.add_message_handler('RBHRB', HRB)

        :param message_id: the ID as string of the message to handle
        :param handler_func: the function to call when a message is received
                             for the specific message_id
        """

        if '$' in message_id:
                raise AssertionError("message_id should not contain a '$'")
        if message_id is not None:
            self.message_handlers[message_id] = handler_func
        else:
            raise AssertionError("Cannot bind a handler find to 'None'")

    def prehandler(self):
        """A decorator that registers a function for to be called before
        message handlers. May be used to modify or suppress messages.
        A prehandler will suppress a message if it lacks a 'return' statement
        or explicitly returns None. Functionally identical to
        :meth:`add_prehandler` but offering a decorator wrapper::

            @NMEAServer.prehandler()
            def prehandler(context, message):
                if message.data[0] == 'S': # Example of message suppression
                    return None #To suppress the message
                if message[1] = 'M': #Example of modifying the message
                    message[2] =  'new value'
                    return message
                else:
                    return message
        """

        def decorator(f):
            self.add_prehandler(f)
            return f
        return decorator

    def add_prehandler(self, function=None):
        """A decorator that registers a function for to be called before
        message handlers. May be used to modify or suppress messages.
        A prehandler will suppress a message if it lacks a 'return' statement
        or explicitly returns None. Functionally identical to
        :meth:`prehandler` decorator.  Passing 'None' as the function
        will remove the existing prehandler

        For example::

            @NMEAServer.prehandler()
            def prehandler(context, message):
                if message.data[0] == 'S': # Example of message suppression
                    return None #To suppress the message
                if message[1] = 'M': #Example of modifying the message
                    message[2] =  'new value'
                    return message
                else:
                    return message

        Is the same as::

            def prehandler(context, message):
                if message.data[0] == 'S': # Example of message suppression
                    return None #To suppress the message
                if message[1] = 'M': #Example of modifying the message
                    message[2] =  'new value'
                    return message
                else:
                    return message
            app.add_prehandler(prehandler)

        :param function: the function to call when a message is received
                             but before handlers are invoked.
        """

        self.message_pre_handler = function

    def posthandler(self):
        """A decorator that registers a function for to be called after the
        message handlers. A posthandler can modify the response and even
        suppress it if it lacks a return statement or explicitly returns None.
        Functionally identical to :meth:`add_posthandler` but offering a
        decorator wrapper::

            @NMEAServer.posthandler()
            def posthandler(context, message, response):
                print("Printing response {}".format(response))
                return response
        """

        def decorator(f):
            self.add_posthandler(f)
            return f
        return decorator

    def add_posthandler(self, function=None):
        """A decorator that registers a function for to be called after the
        message handlers. A posthandler can modify the response and even
        suppress it if it lacks a return statement or explicitly returns None.
        Functionally identical to :meth:`posthandler` decorator.  Passing
        'None' as the function will remove the existing posthandler

        For example::

            @NMEAServer.posthandler()
            def posthandler(context, message, response):
                print("Printing response {}".format(response))
                return response

        Is the same as::

            def posthandler(context, message, response):
                print("Printing response {}".format(response))
                return response
            app.add_posthandler(posthandler)

        :param function: the function to call when a message is received
                             but before handlers are invoked.
        """

        self.message_post_handler = function

    def unknown_message(self):
        """A decorator that registers a function for to be called when an
        unknown message is received. Functionally identical to
        :meth:`add_unknown_message` but offering a decorator wrapper::

            @NMEAServer.unknown_message()
            def unknown(context, message):
                return nmea.format("TXERR, Unknown sentence received")
        """

        def decorator(f):
            self.add_unknown_message(f)
            return f
        return decorator

    def add_unknown_message(self, function=None):
        """A decorator that registers a function for to be called when an
        unknown message is received. Functionally identical to
        :meth:`unknown_message` decorator.  Passing 'None' as the function
        will remove the existing unknown_message handler

        For example::

            @NMEAServer.unknown_message()
            def unknown(context, message):
                return nmea.format("TXERR, Unknown sentence received")

        Is the same as::

            def unknown(context, message):
                return nmea.format("TXERR, Unknown sentence received")
            app.add_unknown_message(unknown)

        :param function: the function to call when an unknown message is
                        received.
        """

        self.missing_handler = function

    def context_creator(self):
        """A decorator that registers a function for creating a connection
        context. Functionally identical to
        :meth:`add_connection_context_creator` but offering a decorator::

            @NMEAServer.context_creator()
            def context(default_context, message):
                default_context['app_name'] = 'demo'
                return default_context
        """

        def decorator(f):
            self.add_context_creator(f)
            return f

        return decorator

    def add_context_creator(self, function=None):
        """Registers a function to be invoked when a new connection is created
        to generate a custom connection context.  Functionally identical
        to :meth:`context_creator` decorator.

        For example::

            @NMEAServer.context_creator()
            def context(default_context, message):
                default_context['app_name'] = 'demo'
                return default_context

        Is the same as::

            def context(default_context, message):
                default_context['app_name'] = 'demo'
                return default_context
            app.add_context_creator(context)


        :param function: the function to call when a connection is created
        """

        self.connection_context_creator = function

    def bad_checksum(self):
        """A decorator that registers a function for handling messages
        with bad checksums. Note that the parameter is a 'raw_message' as
        a string the message cannot be successfully parsed due to the invalid
        checksum.Functionally identical to
        :meth:`add_bad_checksum_handler` but offering a decorator::

            @NMEAServer.bad_checksum()
            def bad_checksum(context, raw_message):
                default_context['app_name'] = 'demo'
                return nmea.format('TDERR,Invalid Checksum received." \
                "Received *26 but correct checksum should have been *A2')
        """

        def decorator(f):
            self.add_bad_checksum_handler(f)
            return f

        return decorator

    def add_bad_checksum_handler(self, function=None):
        """Registers a function to be invoked when a message with a bad
        checksum is received. Functionally identical to
        :meth:`bad_checksum` decorator.

        For example::

            @NMEAServer.bad_checksum()
            def bad_checksum(context, raw_message):
                default_context['app_name'] = 'demo'
                return nmea.format('TDERR,Invalid Checksum received." \
                "Received *26 but correct checksum should have been *A2')

        Is the same as::

            def bad_checksum(context, raw_message):
                default_context['app_name'] = 'demo'
                return nmea.format('TDERR,Invalid Checksum received." \
                "Received *26 but correct checksum should have been *A2')
            app.add_bad_checksum_handler(bad_checksum)


        :param function: the function to call when a connection is created
        """

        self.bad_checksum_message_handler = function

    def error(self):
        """A decorator that registers a function for handling errors.
        Functionally identical to :meth:`add_error_handler`
        but offering a decorator::

            @NMEAServer.error()
            def error(context, raw_message, err):
                print "something went wrong =("
        """

        def decorator(f):
            self.add_error_handler(f)
            return f

        return decorator

    def add_error_handler(self, function=None):
        """Registers a function to be invoked when an error occurs.
        Functionally identical to :meth:`bad_checksum` decorator.

        For example::

            @NMEAServer.error()
            def error(context, raw_message, err):
                print "something went wrong =("

        Is the same as::

            def error(context, raw_message, err):
                print "something went wrong =("
            app.add_error_handler(error)

        :param function: the function to call when a connection is created
        """

        self.error_handler = function

    def response_stream(self):
        """A decorator that registers a function for used to generate a 
        stream of responses without a request. This will only be called
        once for each new connection. Functionally identical to 
        :meth:`add_response_stream` but offering a decorator::

            @NMEAServer.error()
            def error(context, raw_message, err):
                print "something went wrong =("
        """

        def decorator(f):
            self.add_response_stream(f)
            return f

        return decorator

    def add_response_stream(self, function=None):
        """Registers a function for used to generate a stream of responses
        without a request. This will only be called once for each new
        connection. Use the value context['stream'] to loop over to detect
        when to stop streaming messages. Functionally identical to 
        :meth:`response_stream` decorator.

        For example::

            @NMEAServer.response_stream()
            def response_stream(context, wfile):
                while context['stream']:
                    wfile.write(formatter.format("TXMSG,Important"))
                    wfile.flush

        Is the same as::

            def response_stream(context, wfile):
                while context['stream']:
                    wfile.write(formatter.format("TXMSG,Important"))
                    wfile.flush
            app.add_response_stream(response_stream)

        :param function: the function to call when a connection is created
        """

        self.response_streamer = function

    def dispatch(self, raw_message, connection_context):
        """Dispatch the messages received on the NMEAServer socket.
        May be extended, do not override."""

        if self.message_pre_handler is not None:
            raw_message = self.message_pre_handler(connection_context, 
                                                   raw_message)

        try:
            if raw_message == '':
                raise EOFError("Empty message received. Ending comm")

            message = formatter.parse(raw_message)
            sentence_id = message['sentence_id']
            response = None
            try:
                if self.message_handlers[sentence_id] is not None:
                    response = self.message_handlers[sentence_id](
                        connection_context, message)
                else:
                    if self.missing_handler is not None:
                        response = self.missing_handler(
                            connection_context, message)
            except KeyError:
                if self.missing_handler is not None:
                        response = self.missing_handler(
                            connection_context, message)

            if self.message_post_handler is not None:
                self.message_post_handler(
                    connection_context, message, response)
            if not response.endswith("\n"):
                response = response + "\n"
            return response
        except ValueError:
            if self.bad_checksum_message_handler is not None:
                return self.bad_checksum_message_handler(
                    connection_context, raw_message)
        except EOFError as err:
            raise
        except BaseException as err:
            logger.error("Detected exception: {}".format(str(err)))
            if self.error_handler is not None:
                self.error_handler(connection_context, err)
        return None
        

    class MyTCPHandler(SocketServer.StreamRequestHandler):
        """The StreamRequestHandler instance to use to create a NMEAServer"""

        context = {}
        nmeaserver = None

        def __init__(self, request, client_address,
                     server, NMEAServer_instance):
            if NMEAServer_instance is None:
                raise ValueError('nmeaserver cannot be None')

            self.nmeaserver = NMEAServer_instance
            SocketServer.StreamRequestHandler.__init__(
                self, request, client_address, server)

        def default_context(self):
            """Creates a default connection context dictionary"""

            default_context = {}
            default_context['client_address'] = self.client_address[0]
            return default_context

        def handle(self):
            """Handles a request and pass it to NMEAServer.dispatch()"""

            context = self.default_context()
            if self.nmeaserver.connection_context_creator is not None:
                self.context = self.nmeaserver.connection_context_creator(
                    context)

            if self.nmeaserver.response_streamer is not None:
                self.context['stream'] = True
                t = threading.Thread(
                                target = self.nmeaserver.response_streamer,
                                 args = (self.context, self.wfile),
                                 name = "stream-"+str(self.client_address[0]))
                t.daemon = True
                t.start()

            try:
                while not self.nmeaserver.shutdown_flag:
                    poll_obj = select.poll()
                    poll_obj.register(self.rfile, select.POLLIN)
                    
                    poll_result = poll_obj.poll(0)
                    if poll_result: 
                        received = self.rfile.readline().strip()
                        if self.nmeaserver.debug:
                            logger.debug("< " + received)
                        response = self.nmeaserver.dispatch(
                            received, self.context)
    
                        if response is not None:
                            if self.nmeaserver.debug:
                                logger.debug("> " + response)
                            self.wfile.write(format(response))
                            self.wfile.flush()
                    else:
                        time.sleep(0.1)
            except BaseException as e:
                self.context['stream'] = False
                logger.warn("Connection closing")

    class ThreadedTCPServer(SocketServer.ThreadingTCPServer):
        nmeaserver = None

        def __init__(self, server_address, RequestHandlerClass,
                     NMEAServer_instance):
            if NMEAServer_instance is None:
                raise ValueError('nmeaserver cannot be None')

            SocketServer.TCPServer.allow_reuse_address = True
            SocketServer.ThreadingTCPServer.__init__(
                self, server_address, RequestHandlerClass)
            self.nmeaserver = NMEAServer_instance
            self.daemon_threads = True

            logger.info('Server Address: {}:{}'.format(
                str(server_address[0] or "localhost"), str(server_address[1])))

        def finish_request(self, request, client_address):
            """Finish one request by instantiating RequestHandlerClass."""
            self.RequestHandlerClass(
                request, client_address, self, self.nmeaserver)

        def process_request(self, request, client_address):
            """Start a new thread to process the request."""
            t = threading.Thread(target = self.process_request_thread,
                                 args = (request, client_address),
                                 name = "client-"+str(client_address))
            t.daemon = self.daemon_threads
            t.start()

    def start(self):
        self.nmeaserver = self.ThreadedTCPServer(
            (self.host, self.port), NMEAServer.MyTCPHandler, self)
        self.server_thread = threading.Thread(
            name='nmea', target=self.nmeaserver.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def shutdown(self):
        self.shutdown_flag = True
        self.nmeaserver.shutdown()
        self.nmeaserver.server_close()
        self.server_thread.join()