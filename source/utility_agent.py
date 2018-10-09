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
        self.utility_offer = None

    def pre_auction_round(self):
        """ for each step, utility offers at utility profile rate """

        if self.dynamical_pricing is True:
            self.sell_rate_utility = self.price_profile[self.model.step_count]
            price = self.sell_rate_utility
            quantity = 100
            self.utility_offer = [price, quantity, self.id]

        else:
            """ constant priced energy supply """
            price = 10
            quantity = 100
            # TODO: quantity should just saturate the market... so supply should be linked to unsaturated demand
            # otherwise it will become a messy plot
            self.utility_offer = [price, quantity, self.id]

        self.model.auction.offer_list.append(self.utility_offer)
        print("utility offer", self.utility_offer)