import heapq

class RequestQueue:
    """Priority queue implementation for mutual exclusion requests, 
    will ensure correct ordering of requests based on Lamport timestamps."""
    def __init__(self):
        self.queue = []  # Min-heap for requests: (lamport_time, client_id)

    def add_request(self, lamport_time, client_id):
        heapq.heappush(self.queue, (lamport_time, client_id))

    def get_next_request(self):
        return heapq.heappop(self.queue) if self.queue else None

    def is_empty(self):
        return len(self.queue) == 0
