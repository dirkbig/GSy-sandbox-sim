from source import const
import logging
wallet_log = logging.getLogger('run_microgrid.wallet')


class Wallet(object):
    """(crypto?)wallet owned by respective agent"""
    def __init__(self, _unique_id):
        self.id = _unique_id
        self.coin_balance = const.initial_coins_household

    def settle_payment(self, payment):
        if payment <= self.coin_balance:
            self.coin_balance -= payment
            payment_success = True
            wallet_log.info("payment tx was successful, agent %d", self.id)
        else:
            payment_success = False
            wallet_log.warning("payment tx failed, agent %d", self.id)

        return payment_success

    def settle_revenue(self, payment):
        self.coin_balance += payment
        payment_success = True
        wallet_log.info("revenue tx was successful, agent %d", self.id)

        return payment_success
