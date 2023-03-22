import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        self.init(players = sp.map(l={}, tkey= sp.TNat, tvalue=sp.TAddress),
                 ticket_cost = sp.tez(1),
                 tickets_available = sp.nat(5),
                 max_tickets = sp.nat(5),
                 operator = sp.address("tz1KxgFc6knZgc5gipvFqqT59JYMi8o63VdL"),
    )
        
    @sp.entry_point
    def buy_ticket(self, num_tickets):
        sp.set_type(num_tickets, sp.TNat)
        
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.utils.nat_to_mutez(sp.utils.mutez_to_nat(self.data.ticket_cost) * (num_tickets)), "INVALID AMOUNT")
        sp.verify(self.data.tickets_available - num_tickets >= 0, "REQUESTING MORE TICKETS THAN AVAILABLE")      

        self.data.tickets_available = sp.as_nat(self.data.tickets_available - num_tickets)
        
        sp.for _ in sp.range(0, num_tickets, step=1):
            self.data.players[sp.len(self.data.players)] = sp.sender

        new_cost = sp.utils.mutez_to_nat(self.data.ticket_cost) * num_tickets
        extra_balance = sp.amount - sp.utils.nat_to_mutez(new_cost)
        
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")
        
        winner_index = sp.as_nat(sp.now - sp.timestamp(0)) % self.data.max_tickets
        winner_address = self.data.players[winner_index]
        
        sp.send(winner_address, sp.balance)
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_ticket_cost(self, new_cost):
        sp.set_type(new_cost, sp.TNat)
        
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 5, "GAME IS ONGOING")

        self.data.ticket_cost = sp.utils.nat_to_tez(new_cost)

    @sp.entry_point
    def change_max_tickets(self, new_max):
        sp.set_type(new_max, sp.TNat)
        
        sp.verify(sp.sender == self.data.operator, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 5, "GAME IS ONGOING")

        self.data.max_tickets = new_max
        self.data.tickets_available = new_max
    

@sp.add_test(name="Main")
def test():
    scenario = sp.test_scenario()

    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")
    charles = sp.test_account("charles")
    john = sp.test_account("john")

    lottery = Lottery()
    scenario += lottery

    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.change_ticket_cost(2).run(sender=admin)

    
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(4), sender = alice)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(2), sender = bob)
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(3), sender = john, valid = False)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = charles, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(21).run( now = sp.timestamp(2), sender = admin)
