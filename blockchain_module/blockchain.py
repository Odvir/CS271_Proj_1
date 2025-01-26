import socket
import hashlib
import threading
import time
from .block import Block


class Blockchain:
    """Class made to represent a blockchain, storing blocks in a linked list.
    Supports adding blocks, validating the chain, and retrieving the last block."""
    def __init__(self):
        self.chain = []

    def add_block(self, operation):
        prev_block = self.chain[-1] if self.chain else None
        prev_hash = prev_block.hash if prev_block else "0"  # "0" for genesis block
        new_block = Block(operation, prev_hash)
        self.chain.append(new_block)
        return new_block

    def print_chain(self):
        for block in self.chain:
            sender, receiver, amount = block.operation
            print(f"Sender: {sender}, Receiver: {receiver}, Amount: {amount}, Hash: {block.hash}")

    def get_last_block(self):
        # Return the last block in the chain, or None if empty
        return self.chain[-1] if self.chain else None

    def is_valid_chain(self):
        # Validate the integrity of the blockchain
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.prev_hash != previous.hash:
                return False
        return True
