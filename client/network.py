import socket
import threading
import json

class Network:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.id = port % 1000
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)  # Allows up to 4 connections, one more than needed to be safe
        self.connections = {}  # Keep track of active connections {client_name: (conn, addr)}
        self.buffers = {} # Buffer for each client to store incoming messages
    
    def add_connection(self, client_name, host, port):
        """Establish a connection to a peer."""
        addr = (host, port)
        try:
            if port > 7000:
                print(f"Skipping connection to {host}:{port}")
                return
            conn = socket.create_connection((host, port))
            self.connections[client_name] = (conn, addr) 
            print(f"Connected to {host}:{port}")
        except Exception as e:
            print(f"Failed to connect to {host}:{port} - {e}")

    def start_server(self, handler_function):
        """Start the server to handle incoming connections."""
        print(f"Server started on {self.host}:{self.port}")
        while True:
            conn, addr = self.socket.accept()
            print(f"New connection from {addr}")
            # You can use the `addr` or map it to a specific client name here
            # For simplicity, we're associating it with a unique client name or ID
            client_name = f"Client-{addr[1]}"  # Just an example, you can use an actual mapping
            self.connections[client_name] = (conn, addr)
            threading.Thread(target=self.handle_client, args=(conn, addr, handler_function)).start()

    def send_message(self, client_name, message):
        """Send a message to a specific client identified by client_name."""
        if client_name not in self.connections:
            print("current live connections: ", self.connections)
            print(f"No active connection to {client_name}")
            return
        conn, addr = self.connections[client_name]
        try:
            conn.sendall(json.dumps(message).encode("utf-8") + b"\n")
            print(f"Message {message} sent to {client_name} at {addr}")
        except Exception as e:
            print(f"Failed to send message to {client_name} - {e}")
            self.close_connection(client_name)

    def handle_client(self, conn, addr, handler_function):
        """Handles communication with a specific client."""
        while True:
            msg = self.receive_message(conn)
            if not msg:
                print(f"Connection from {addr} closed")
                break
            handler_function(conn, addr, msg)
        conn.close()

    def broadcast_message(self, message):
        """Sends a message to all active connections."""
        print(f"Broadcasting message from {message['sender']}")
        for client_name, (conn, addr) in self.connections.items():
            try:
                conn.sendall(json.dumps(message).encode("utf-8") + b"\n")
                print(f"Message broadcast to {client_name} at {addr}")
            except BrokenPipeError:
                print(f"Connection to {client_name} is broken, removing...")
                self.connections.pop(client_name)
                conn.close()

    def receive_message(self, conn):
        """
        Block until exactly one JSON message can be parsed from the connection,
        or until the connection is closed (in which case return None).
        """
        # print("print in rec_msg: ", threading.current_thread().name, conn,  flush=True) 
        if conn not in self.buffers:
            self.buffers[conn] = b""

        while True:
            # First, see if there's already a complete JSON object in self.buffers[conn].
            msg, leftover = self.try_parse_one_message(self.buffers[conn])
            if msg is not None:
                # Found one complete JSON object in the buffer
                self.buffers[conn] = leftover  # store any leftover bytes
                return msg

            # No complete JSON message yet, so read more data from socket
            chunk = conn.recv(1024)
            if not chunk:
                # Connection closed, no more data
                return None

            # Accumulate the newly-read data
            self.buffers[conn] += chunk

    def try_parse_one_message(self, buffer: bytes):
        """
        Attempt to parse EXACTLY one JSON message from the front of `buffer`.
        Return (messageDict, leftoverBytes) if successful, or (None, buffer) if not enough data.

        A simple approach: use newline-delimited JSON, or do a "look for one balanced JSON object".
        """
        # -- Option A: If using newline-delimited JSON:
        if b"\n" not in buffer:
            return None, buffer  # no complete JSON line yet

        line, leftover = buffer.split(b"\n", 1)  # split on the first newline only
        line = line.strip()
        if not line:
            # If the line is empty, skip and keep going
            return None, leftover

        # Attempt JSON parse
        try:
            msg_dict = json.loads(line.decode("utf-8"))
            return msg_dict, leftover
        except json.JSONDecodeError:
            # Not a valid JSON string yet (or malformed).
            # Possibly you want to handle errors or keep reading.
            return None, buffer
        
    def close_connection(self, client_name):
        """Closes a specific connection to a client."""
        if client_name in self.connections:
            conn, addr = self.connections[client_name]
            conn.close()
            del self.connections[client_name]
            print(f"Connection to {client_name} at {addr} closed")
    def shutdown(self):
        """Closes all active connections and shuts down the server."""
        print(f"Shutting down {self.id} network...")
        for addr, conn in self.connections.items():
            conn.close() 
        self.socket.close()  # close the listening socket
        self.connections.clear()  # clear the connection dictionary
        print(f"{self.id} network shut down")
