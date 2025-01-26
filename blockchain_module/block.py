import socket
import hashlib
import threading
import time

class Block:
    """Class made to represent a block in the blockchain.
    * Each block contains only one transaction.
    * operation: (<sender, receiver, amount>) and hash pointers.
    * prev_hash: This hash is a pair consisting of a pointer to previous block and the hash of the content of the previous block
        On+1.Hash = SHA256(On.Operation||On.Hash)"""
    def __init__(self, operation, prev_hash):
        self.operation = operation # Tuple: (sender, receiver, amount) (REQUIREMENT)
        self.prev_hash = prev_hash # On+1.Hash = SHA256(On.Operation||On.Hash) (REQUIREMENT)
        self.hash = self.compute_hash()

    def compute_hash(self):
        # Combine operation details and previous hash for the current hash
        content = f"{self.operation[0]}{self.operation[1]}{self.operation[2]}{self.prev_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self):
        sender, receiver, amount = self.operation
        return (f"Block(Sender={sender}, Receiver={receiver}, Amount={amount}, "
                f"Hash={self.hash})")
