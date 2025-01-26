class BalanceTable:
    """Class made to Manage a dictionary of balances for each client.
    Verifies and updates balances during transactions."""
    def __init__(self, initial_balances):
        self.table = initial_balances  # Dictionary: {client_name: balance} (REQUIREMENT)
    def get_balance(self, client):
        return self.table.get(client, 0)
    def get_whole_table(self):
        return self.table
    def update_init_balance(self, client, amount):
        self.table[client] = amount
    def update_balance(self, sender, receiver, amount):
        print(self.table)
        if self.table[sender] < amount:
            raise ValueError("Insufficient funds")
        self.table[sender] -= amount
        self.table[receiver] = self.get_balance(receiver) + amount
        print(f"Balance updated in {sender}'s account. {sender}'s new Balance Table : {self.table}")
