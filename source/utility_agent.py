from mesa import Agent
from source.wallet import Wallet

import numpy as np
import logging
utility_log = logging.getLogger('run_microgrid.utility grid')


class UtilityAgent(Agent):
    """ Utility agent is created by calling this function, functions as a market maker in energy community """
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

        self.price_sell = self.utility_selling_price_fix
        self.price_buy = self.utility_buying_price_fix

        self.wallet = Wallet(self.id)

    def pre_auction_round(self):
        """ for each step, utility offers at utility profile rate """

        if self.dynamical_pricing is True:
            self.price_sell = self.price_profile[self.model.step_count] + self.utility_buying_price_fix
            self.price_buy = self.price_profile[self.model.step_count] + self.utility_buying_price_fix

        else:
            """ constant priced energy supply """
            self.price_sell = self.utility_selling_price_fix
            self.price_buy = self.utility_buying_price_fix

        """ two ways for utility to shoot its energy offer into the market:
            announcing a market maker rate, auctioneer assuming infinite supply capacity
             or announcing a price_quantity bid (quantity being rather high/large of course) """
        # self.model.auction.offer_list.append(self.utility_offer)
        self.model.auction.utility_market_maker_rate = self.price_sell
        self.sell_rate_utility = self.price_sell
        self.buy_rate_utility = self.price_buy

        # The bids and offers of the utility grid are set in "microgrid_environment.py" according to the total demand
        # and offer for each time step.
        self.bids = None
        self.offers = None

        # If there is a utility grid track the selling price of the grid.
        self.model.data.utility_price[self.model.step_count] = self.price_sell

    """ this function should only be called after ALL agents have been able to post bids/offers """
    def append_utility_offer(self, bid_list, offer_list):
        """ function is only called when an utility is present, it supplements the offer list of auctioneer
            with an 'infinite (i.e. saturated)' supply of energy up to the necessary amount to cover all demand,
            bought or not """

        # try:
        #     bid_total = sum(np.asarray(bid_list, dtype=object)[:, 1])
        # except IndexError:
        #     utility_log.info("no consumers in the grid demanding energy")
        #     return

        bid_total = 0
        for bid in bid_list:
            if bid:
                bid_total += bid[1]

        try:
            prosumer_offer_total = sum(np.asarray(offer_list, dtype=object)[:, 1])
        except IndexError:
            prosumer_offer_total = 0
            utility_log.info("no prosumers in the grid supplying energy")

        """ Append utility"""

        def empty(seq):
            try:
                return all(map(empty, seq))
            except TypeError:
                return False

        total_offer_below_mmr = 0
        utility_id = self.model.agents['Utility'].id
        if empty(offer_list) is True:
            utility_quantity = bid_total
            self.model.auction.offer_list.insert(0, [self.price_sell, utility_quantity, utility_id])
            print('Energy offered by {} is {}'.format(self.id, utility_quantity))

        else:
            offer_index = 0
            for offer in offer_list:
                try:
                    if offer[0] <= self.price_sell:
                        """ offer is less expensive than market maker rate """
                        total_offer_below_mmr += offer[1]
                        pass
                except IndexError:
                    pass
                if offer[0] > self.price_sell or offer_index == len(offer_list) - 1:
                    """ offer is more expensive that market maker rate, 
                        utility is only activated if market maker rate is competitive (lower than prosumer rate)"""
                    if bid_total > total_offer_below_mmr:
                        utility_quantity = bid_total - total_offer_below_mmr
                        self.model.auction.offer_list.insert(offer_index + 1, [self.price_sell, utility_quantity, utility_id])
                        print('Energy offered by {} is {}'.format(self.id, self.offers))

                    else:
                        utility_log.info("no utility import into community needed at this step")
                offer_index += 1

        return bid_list, offer_list

    def post_auction_round(self):
        this_energy_trade = sum(self.model.auction.who_gets_what_dict[self.id])
        if this_energy_trade < 0:
            self.energy_sold_tot += abs(this_energy_trade)
        elif this_energy_trade > 0:
            self.energy_bought_tot += this_energy_trade

        traded_energy = sum(self.model.auction.who_gets_what_dict[self.id])
        self.model.data.agent_measurements[self.id]["traded_volume_over_time"][self.model.step_count] = traded_energy
        return

    def alternative_pricing(self):

        assert self.model.data.fit_pricing is True
        # maximum feed in volume based on yearly number
        max_feed_in = 10000000
        # Feed-in-Tariff
        fit = 0.5 * self.price_sell

        for agent in self.model.agents:
            feed_in_production_from_agent = max(agent.rest_production, max_feed_in)
            reimbursement_fit = feed_in_production_from_agent * fit
            agent.wallet.settle_revenue(reimbursement_fit)
            self.wallet.settle_revenue(reimbursement_fit)

    def track_data(self):
        pass
