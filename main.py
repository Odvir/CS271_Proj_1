import json
import threading
import time
from client.client import Client
# Load configuration from the JSON file
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Main function to initialize and test clients
def main():
    # Load client configurations
    config_file = "config/clients.json"
    client_configs = load_config(config_file)
    # Create clients from configurations
    clients = {}
    for config in client_configs:
        name = config["name"]
        host = config["ip"]
        port = config["port"]

        # Exclude self when passing peers
        peers = [peer for peer in client_configs if peer["name"] != name]
        print(peers)
        # Initialize the client with its peers
        clients[name] = Client(name, host, port, peers)

    # Start each client's server in a separate thread
    for client in clients.values():
        threading.Thread(target=client.start, daemon=True).start()
    # wait to ensure clients started
    time.sleep(1)
    print("Simulating transactions...")
    clients["ClientA"].handle_transaction(("ClientA", "ClientB", 5), True)  # A -> B: $5

    time.sleep(2)
    print("Printing balances...")
    for client in clients.values():
        print(f"{client.name}:")
        client.print_whole_table()

if __name__ == "__main__":
    main()
