from mesa import Agent
from source.wallet import Wallet

import logging
utility_log = logging.getLogger('run_microgrid.utility grid')


class UtilityAgent(Agent):
    """ Utility agent is created by calling this function """
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)

        self.model = model
        self.trading_state = 'undefined'
        self.id = _unique_id
        self.dynamical_pricing = False

        """load in utility energy price profile"""
        self.price_profile = self.model.data.utility_pricing_profile
        self.sell_rate_utility = None
        self.utility_offer = None

        self.wallet = Wallet(self.id)

    def pre_auction_round(self):
        """ for each step, utility offers at utility profile rate """

        if self.dynamical_pricing is True:
            self.sell_rate_utility = self.price_profile[self.model.step_count]
            price = self.sell_rate_utility
            # quantity = 1000
            # self.utility_offer = [price, quantity, self.id]

        else:
            """ constant priced energy supply """
            price = 9
            # TODO: quantity should just saturate the market... so supply should be linked to unsaturated demand
            # quantity = 1000
            # otherwise it will become a messy plot
            # self.utility_offer = [price, quantity, self.id]

        self.model.auction.utility_market_maker_rate = price

    def post_auction_round(self):
        return
