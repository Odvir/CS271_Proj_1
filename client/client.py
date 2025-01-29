from client.network import Network
from blockchain_module.blockchain import Blockchain
from client.balance_table import BalanceTable
from client.lamport import LamportClock
from client.request_queue import RequestQueue
import threading
import time

def run_client(name, host, port, peers, first):
        """
        This function runs in its own process. It creates a single Client instance,
        starts its server, connects to peers if 'first' is True, etc.
        """
        from client.client import Client  # or an absolute import

        client = Client(name, host, port, peers, first)
        client.start()  # This starts the client's network server thread, etc.

        if name == "ClientA":
            print("Simulating transaction from ClientA -> ClientB")
            client.handle_transaction(("ClientA", "ClientB", 5), True)
            time.sleep(2)
            print("Final balances as seen by ClientA:")
            client.print_whole_table()

        # Keep this process alive
        while True:
            time.sleep(1)

class Client:
    """Class to represent a client in the blockchain network.
    * Each client has a name, host, port, blockchain, network, lamport logical clock, and balance table.
    """
    def __init__(self, name, host, port, peers, first):
        self.name = name 
        self.host = host
        self.port = port
        self.first = first
        self.peers = peers  # List of other clients' configurations
        self.blockchain = Blockchain()
        self.network = Network(host, port)
        self.id = port % 1000
        self.lamport_clock = LamportClock(port % 1000) #port % 1000 is the client_id
        self.request_queue = RequestQueue()  # Priority queue for Lamport mutex requests
        self.mutex_held = False  # Whether this client holds the mutex
        self.mutex_request_handler = threading.Lock()  # New mutex to handle incoming mutex requests
        self.acks_count = 0  # Number of acknowledgements received from other client peers, as we maintain a connection to all
        self.real_connection_count = 0
        self.balance_table = BalanceTable({name: 10}) #starting out with a balance of 10$ (REQUIREMENT)
        self.ack_event = threading.Event()
        self.mutex_release_event = threading.Event()

    def request_mutex(self):
        """Request access to the critical section (mutex)."""
        print(f"{self.name} is requesting the mutex")
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

    def handle_transaction(self, operation, first_request=False):
        """Handles a transaction request."""
        print(f"client name: {self.name} received operation: {operation}") 
        try:
            # Request mutex before accessing the critical section
            # print(f"{self.name} is requesting the mutex to handle transaction {operation}")
            sender, receiver, amount = operation

            # self.request_mutex()
            print(f"{self.name} has acquired the mutex to handle transaction {operation}")
            # Critical section: Validate and execute the transaction
            self.balance_table.update_balance(sender, receiver, amount)
            self.blockchain.add_block(operation)
            print(f"Transaction SUCCESS: {sender} sent ${amount} to {receiver}")

            self.lamport_clock.increment()

            # Broadcast the transaction to peers
            message = {"type": "transaction", "operation": operation, "lamport_time": self.lamport_clock.get_time(), "sender": self.name}
            # Release the mutex after the transaction is complete
            # self.release_mutex()
            if first_request:
                self.network.broadcast_message(message)
        except ValueError as e:
            print(f"Transaction FAILED: {e}")

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
                self.balance_table.update_init_balance(peer['name'], 10)
                self.real_connection_count += 1
            except Exception as e:
                print(f"{self.name} failed to connect to {peer['name']}: {e}")

    def print_balances(self):
        print(self.balance_table.get_balance(self.name))
    
    def print_whole_table(self):
        print(self.balance_table.get_whole_table())

    def handle_msg(self, conn, addr, msg):
        """Handles incoming messages from the network. If balance request, sends balance response.
        If transaction, processes the transaction by calling handle_transaction."""
        print("print in handle_msg: ", threading.current_thread().name, conn,  flush=True) 
        if msg:
            if msg["type"] == "transaction":
                print(f"{self.name} received transaction message")
                sender, receiver, amount = msg["operation"]
                received_clock, sender_id = msg["lamport_time"]
                self.lamport_clock.sync(received_clock, sender_id)
                self.handle_transaction(msg["operation"])
                # else:
                #     self.balance_table.update_balance(sender, receiver, amount)
                #     print(f"{self.name} received ${amount} from {sender}")
            elif msg["type"] == "mutex_request":
                # Add request to the queue and send ACK
                print(f"{self.name} received mutex request")
                # Acquire the mutex_request_handler to ensure we handle one request at a time
                sender = msg["sender"]
                print(f"{self.name}: The mutex is currently held: {self.mutex_held}")
                if not self.mutex_held:
                    # Add request to the queue
                    self.request_queue.add_request(self.lamport_clock.get_time(), sender)
                    received_clock, sender_id = msg["lamport_time"]
                    self.lamport_clock.sync(received_clock, sender_id)
                    time.sleep(1)
                    
                    # Only send an ACK if it's the first request in the queue
                    first_request = self.request_queue.peek_next_request()
                    print(f"This is {self.name} and this is the first request in the queue: {first_request}, and this is the whole queue: {self.request_queue.queue}")
                    if first_request and first_request[1] == sender:
                        print(f"{self.name} sending ACK to {sender}")
                        self.request_queue.get_next_request()
                        self.lamport_clock
                        ack_message = {"type": "mutex_ack", "lamport_time": self.lamport_clock.get_time(), "sender": self.name}
                        self.network.send_message(sender, ack_message)
                        print("ACK sent by ", self.name)
                        time.sleep(5)
                        # self.mutex_release_event.wait()
                    else:
                        print(f"{self.name} skipping ACK for {sender}, request is not first in the queue.")
                else:
                    print(f"{self.name} is holding the mutex. Skipping ACK for {msg['sender']}.")

            elif msg["type"] == "mutex_ack":
                # Decrement pending ACK count
                self.acks_count += 1
                print(f"{self.name} received ACK from {msg['sender']}. ACKs count: {self.acks_count} out of {self.real_connection_count}")
                if self.acks_count == self.real_connection_count:
                    # If all ACKs received, release the mutex
                    self.ack_event.set()

            elif msg["type"] == "mutex_release":
                # Remove the releasing client's request from the queue
                print(f"{self.name} received mutex release")
                self.mutex_held = False
                released_request = self.request_queue.get_next_request()
                self.mutex_release_event.set()
                print(f"Request {released_request} has been processed")

            elif msg["type"] == "balance_request":
                sender = msg["sender"]
                balance = self.balance_table.get_balance(self.name)
                response = {"type": "balance_response", "balance": balance}
                self.network.send_message(sender, response)
        

