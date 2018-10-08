from mesa import Agent
import logging
utility_log = logging.getLogger('utility grid')


class UtilityAgent(Agent):
    """ Utility agent is created by calling this function """
    def __init__(self, model):
        self.model = model
        self.id = 'utility'
        self.dynamical_pricing = False

        """load in utility energy price profile"""
        self.price_profile = self.model.data.utility_pricing_profile
        self.sell_rate_utility = None
        self.utility_bid = None

    def utility_pre_auction_step(self):
        """ for each step, utility offers at utility profile rate """

        if self.dynamical_pricing is True:
            self.sell_rate_utility = self.price_profile[self.model.step_count]
            price = self.sell_rate_utility
            quantity = 100
            self.utility_bid = [price, quantity, self.id]

        else:
            """ constant priced energy supply """
            price = 0.30
            quantity = 100
            # TODO: quantity should just saturate the market... so supply should be linked to unsaturated demand
            self.utility_bid = [price, quantity, self.id]
