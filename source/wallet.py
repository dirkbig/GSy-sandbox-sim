import numpy as np
import logging
wallet_log = logging.getLogger('run_microgrid.wallet')


class Wallet(object):
    """(crypto?)wallet owned by respective agent"""
    def __init__(self, _unique_id):
        self.id = _unique_id
        self.coin_balance = 10000000
        self.payment_history = {}

    def settle_payment(self, payment, step_count):
        if payment <= self.coin_balance:
            self.coin_balance -= payment
            # self.payment_history.append([-payment, step_count])
            try:
                self.payment_history[step_count] -= payment
            except KeyError:
                self.payment_history[step_count] = -payment

            wallet_log.info("payment tx was successful, agent {}".format(self.id))
        else:
            wallet_log.warning("payment tx failed, agent {}".format(self.id))
            exit("add handler for this")

    def settle_revenue(self, payment, step_count):
        self.coin_balance += payment
        wallet_log.info("revenue tx was successful, agent {}".format(self.id))
        # self.payment_history.append([payment, step_count])
        try:
            self.payment_history[step_count] += payment
        except KeyError:
            self.payment_history[step_count] = payment

