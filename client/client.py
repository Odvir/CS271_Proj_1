from client.network import Network
from blockchain_module.blockchain import Blockchain
from client.balance_table import BalanceTable
from client.lamport import LamportClock
from client.request_queue import RequestQueue
import threading
import time

class Client:
    """Class to represent a client in the blockchain network.
    * Each client has a name, host, port, blockchain, network, lamport logical clock, and balance table.
    """
    def __init__(self, name, host, port, peers):
        self.name = name 
        self.host = host
        self.port = port
        self.peers = peers  # List of other clients' configurations
        self.blockchain = Blockchain()
        self.network = Network(host, port)
        self.id = port % 1000
        self.lamport_clock = LamportClock(port % 1000) #port % 1000 is the client_id
        self.request_queue = RequestQueue()  # Priority queue for Lamport mutex requests
        self.mutex_held = False  # Whether this client holds the mutex
        self.acks_count = 0  # Number of acknowledgements received from other client peers, as we maintain a connection to all
        self.real_connection_count = 0
        self.balance_table = BalanceTable({name: 10}) #starting out with a balance of 10$ (REQUIREMENT)
        self.ack_event = threading.Event()
    
    def request_mutex(self):
        """Request access to the critical section (mutex)."""
        self.lamport_clock.increment()
        self.mutex_held = False
        # add my request to the queue that I HOLD
        self.request_queue.add_request(self.lamport_clock.get_time(), self.name)
        request_message = {
            "type": "mutex_request",
            "lamport_time": self.lamport_clock.get_time(),
            "sender": self.name,
        }
        self.network.broadcast_message(request_message)
        time.sleep(3)
        self.ack_event.wait()
        self.mutex_held = True
        print(f"{self.name} has acquired the mutex")

    def release_mutex(self):
        """Release access to the critical section and notify peers."""
        self.mutex_held = False
        print(f"{self.name} is releasing the mutex")
        self.lamport_clock.increment()

        # Remove own request from the queue
        self.request_queue.get_next_request()

        release_message = {"type": "mutex_release", "lamport_time": self.lamport_clock.get_time(), "sender": self.name}
        self.network.broadcast_message(release_message)

    def handle_transaction(self, operation):
        """Handles a transaction request."""
        try:
            # Request mutex before accessing the critical section
            print(f"{self.name} is requesting the mutex to handle transaction {operation}")
            self.request_mutex()

            # Critical section: Validate and execute the transaction
            sender, receiver, amount = operation
            self.balance_table.update_balance(sender, receiver, amount)
            self.blockchain.add_block(operation)
            print(f"Transaction SUCCESS: {sender} sent ${amount} to {receiver}")

            self.lamport_clock.increment()

            # Broadcast the transaction to peers
            message = {"type": "transaction", "operation": operation, "lamport_time": self.lamport_clock.get_time(), "sender": self.name}
            self.network.broadcast_message(message)
        except ValueError as e:
            print(f"Transaction FAILED: {e}")
        finally:
            # Release the mutex after the transaction is complete
            self.release_mutex()

    def start(self):
        # self.connect_to_peers()
        threading.Thread(target=self.network.start_server, args=(self.handle_msg,)).start()
        # Connect to peers
        self.connect_to_peers()

    def connect_to_peers(self):
        """Connect to all peer clients."""
        for peer in self.peers:
            addr = (peer["ip"], peer["port"])
            # Prevent self-connection
            if addr == (self.host, self.port):  # Prevent self-connection
                print(f"{self.name} skipping connection to self.")
                continue
            # Prevent redundant connections
            if addr in self.network.connections:
                print(f"{self.name} already connected to {peer['name']}")
                continue
            try:
                print(f"{self.name} connecting to {peer['name']} at {peer['ip']}:{peer['port']}")
                self.network.add_connection(peer['name'], peer["ip"], peer["port"])
                self.real_connection_count += 1
            except Exception as e:
                print(f"{self.name} failed to connect to {peer['name']}: {e}")

    def print_balances(self):
        print(self.balance_table.get_balance(self.name))

    def handle_msg(self, conn, addr):
        """Handles incoming messages from the network. If balance request, sends balance response.
        If transaction, processes the transaction by calling handle_transaction."""
        msg = self.network.receive_message(conn)
        print(f"{self.name} received message: {addr}")
        if msg:
            if msg["type"] == "transaction":
                received_clock, sender_id = msg["lamport_time"]
                self.lamport_clock.sync(received_clock, sender_id)
                self.handle_transaction(msg["operation"])
            elif msg["type"] == "mutex_request":
                # Add request to the queue and send ACK
                lamport_time = msg["lamport_time"]
                sender = msg["sender"]
                self.request_queue.add_request(lamport_time, sender)

                # Send an ACK back to the requester
                print(f"{self.name} received request from {sender}. Sending ACK...")
                ack_message = {"type": "mutex_ack", "lamport_time": self.lamport_clock.get_time(), "sender": self.name}
                self.network.send_message(sender, ack_message)

            elif msg["type"] == "mutex_ack":
                # Decrement pending ACK count
                self.acks_count += 1
                print(f"{self.name} received ACK from {msg['sender']}. ACKs count: {self.acks_count}")
                if self.acks_count == self.real_connection_count:
                    # If all ACKs received, release the mutex
                    self.ack_event.set()

            elif msg["type"] == "mutex_release":
                # Remove the releasing client's request from the queue
                released_request = self.request_queue.get_next_request()
                print(f"Request {released_request} has been processed")

            elif msg["type"] == "balance_request":
                client_name = msg["client"]
                balance = self.balance_table.get_balance(client_name)
                response = {"type": "balance_response", "balance": balance}
                self.network.send_message(addr[0], addr[1], response)
        

