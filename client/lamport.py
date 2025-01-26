class LamportClock:
    """Class to implement Lamport clock logic to handle distributed event ordering.
    Also synchronizes clocks between clients during communication.

    From PDF:
        "Each client maintains a Lamport logical clock. As discussed in the lecture, 
        we should use the Totally-Ordered Lamport Clock, i.e.
        ⟨Lamportclock, Processid⟩, to break ties, and each client should maintain
        its request queue/blockchain"
        """
    def __init__(self, client_id):
        self.clock = 0
        self.process_id = client_id

    def increment(self):
        self.clock += 1

    def sync(self, received_clock, sender_id):
        """
        Synchronize the Lamport clock with an incoming clock value.
        Args:
            received_clock (int): The logical clock received from another process.
            sender_id (int): The process ID of the sender.
        """
        # Update the clock with the maximum value, and increment by 1.
        if (received_clock, sender_id) > (self.clock, self.process_id):
            self.clock = received_clock
        self.clock += 1

    def get_time(self):
        return (self.clock, self.process_id)
    def __repr__(self):
        """
        Represent the LamportClock object for debugging purposes.
        """
        return f"LamportClock(clock={self.clock}, process_id={self.process_id})"
    
