from source import const


class Wallet(object):
    """(crypto?)wallet owned by respective agent"""
    def __init__(self, _unique_id):
        self.id = _unique_id
        self.coin_balance = const.initial_coins_household

    def settle_payment(self, payment):
        # TODO: link this to settlement of agents/auctioneers
        # TODO: link this to a budget check before bidding
        if payment >= self.coin_balance:
            self.coin_balance -= payment
            payment_success = True
        else:
            payment_success = False
        return payment_success
