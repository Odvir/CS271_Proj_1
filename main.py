import json
import threading
import time
from client.client import Client, run_client
import multiprocessing
# Load configuration from the JSON file
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Main function to initialize and test clients
def main():
    config_file = "config/clients.json"
    client_configs = load_config(config_file)

    processes = []
    # 1. Create all processes (but don't start them yet)
    for config in client_configs:
        name  = config["name"]
        host  = config["ip"]
        port  = config["port"]
        peers = [peer for peer in client_configs if peer["name"] != name]
        first = (name == "ClientA")
        
        p = multiprocessing.Process(
            target=run_client,  # your function that runs a single client
            args=(name, host, port, peers, first)
        )
        processes.append(p)

    # 2. Start all processes
    for p in processes:
        p.start()

    try:
        # 3. Wait for all processes to finish or be interrupted
        for p in processes:
            p.join()  # This will block until the process finishes
    except KeyboardInterrupt:
        # 4. If user hits Ctrl+C, terminate all processes forcibly
        print("Caught KeyboardInterrupt! Terminating child processes...")
        for p in processes:
            p.terminate()
    finally:
        # 5. Just in case any are still alive or we want a final cleanup
        for p in processes:
            if p.is_alive():
                p.terminate()
        # Optionally join again for a clean exit
        for p in processes:
            p.join()

        print("All child processes terminated. Exiting.")


if __name__ == "__main__":
    main()
