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
        self.dynamical_pricing = self.model.data.utility_dynamical_pricing

        """ Track values """
        self.energy_bought_tot = 0
        self.energy_sold_tot = 0

        """load in utility energy price profile"""
        self.price_profile = self.model.data.utility_pricing_profile
        self.utility_selling_price_fix = self.model.data.utility_selling_price_fix
        self.utility_buying_price_fix = self.model.data.utility_buying_price_fix
        self.sell_rate_utility = None
        self.buy_rate_utility = None
        self.utility_offer = None
        # Bid in the format [price, quantity, self ID]
        self.bids = None
        self.offers = None

        self.wallet = Wallet(self.id)

    def pre_auction_round(self):
        """ for each step, utility offers at utility profile rate """

        if self.dynamical_pricing is True:
            price_sell = self.price_profile[self.model.step_count] + self.utility_buying_price_fix
            price_buy = self.price_profile[self.model.step_count] + self.utility_buying_price_fix
            # quantity = 1000
            # self.utility_offer = [price, quantity, self.id]

        else:
            """ constant priced energy supply """
            price_sell = self.utility_selling_price_fix
            price_buy = self.utility_buying_price_fix
            # TODO: quantity should just saturate the market... so supply should be linked to unsaturated demand
            # quantity = 1000
            # otherwise it will become a messy plot
            # self.utility_offer = [price, quantity, self.id]

        """ two ways for utility to shoot its energy offer into the market:
            announcing a market maker rate, auctioneer assuming infinite supply capacity
             or announcing a price_quantity bid (quantity being rather high/large of course) """
        # self.model.auction.offer_list.append(self.utility_offer)
        self.model.auction.utility_market_maker_rate = price_sell
        self.sell_rate_utility = price_sell
        self.buy_rate_utility = price_buy

        # The bids and offers of the utility grid are set in "microgrid_environment.py" according to the total demand
        # and offer for each time step.
        self.bids = None
        self.offers = None

        # print("utility offer", self.utility_offer)

    def post_auction_round(self):
        this_energy_trade = sum(self.model.auction.who_gets_what_dict[self.id])
        if this_energy_trade < 0:
            self.energy_sold_tot += abs(this_energy_trade)
        elif this_energy_trade > 0:
            self.energy_bought_tot += this_energy_trade

        return
