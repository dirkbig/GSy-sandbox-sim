from mesa import Model
from auctioneer_agent import PayAsClearAuctioneer
from household_agent import HouseholdAgent
from data import Data
import random

import logging
env_log = logging.getLogger('microgrid_env')


class MicroGrid(Model):
    """ Agents are created in this environment that runs the simulation"""
    def __init__(self, _auction_type):
        # TODO: make data instance for each agent
        self.data = Data()
        self.agents = []
        self.num_households = self.data.N
        self.auction_type = _auction_type

        """ create the auction platform"""
        if self.auction_type == 'pay_as_clear':
            self.auction = PayAsClearAuctioneer(self.auction_type, self)

        """ create N agents """
        for i in range(self.num_households):
            # TODO: agents should only receive and use their own data, now they get access to total self.data
            agent = HouseholdAgent(i, self.data)
            self.agents.append(agent)

    def sim_step(self):
        """advance the model by one step"""

        # TODO: iteration of agents converging to an optimum in a While loop?
        random.shuffle(self.agents)
        bid_list = []
        offer_list = []
        for agent in self.agents[:]:
            agent.pre_auction_step()
            if agent.trading_state == 'buying':
                assert agent.offer is None
                bid_list.append(agent.bid)
            if agent.trading_state == 'supplying':
                assert agent.bid is None
                offer_list.append(agent.offer)

        self.auction.auction_round(bid_list, offer_list)




