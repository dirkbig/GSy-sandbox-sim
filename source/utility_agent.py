from mesa import Agent
import logging
utility_log = logging.getLogger('utility grid')


class UtilityAgent(Agent):
    """ Utility agent is created by calling this function """
    def __init__(self, model):
        self.model = model

        """load in utility eneryg price profile"""
        self.price_profile = self.model.data.utility_pricing_profile
        self.sell_rate_utility = None

    def utility_pre_auction_step(self):
        """ for each step, utility offers at utility profile rate """
        sell_rate_utility = self.price_profile[self.model.step_count]
        # offer_utility_supply =
