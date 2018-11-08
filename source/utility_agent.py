from mesa import Agent
from source.wallet import Wallet

import logging
utility_log = logging.getLogger('run_microgrid.utility grid')


class UtilityAgent(Agent):
    """ Utility agent is created by calling this function """
    def __init__(self, model):
        self.model = model
        self.id = 'utility'
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
            quantity = 1000
            self.utility_offer = [price, quantity, self.id]

        else:
            """ constant priced energy supply """
            price = 10
            quantity = 1000
            # TODO: quantity should just saturate the market... so supply should be linked to unsaturated demand
            # otherwise it will become a messy plot
            self.utility_offer = [price, quantity, self.id]

        """ two ways for utility to shoot its energy offer into the market:
            announcing a market maker rate, auctioneer assuming infinite supply capacity
             or announcing a price_quantity bid (quantity being rather high/large of course) """
        # self.model.auction.offer_list.append(self.utility_offer)
        self.model.auction.utility_market_maker_rate = price

        print("utility offer", self.utility_offer)

    def post_auction_round(self):
        return
