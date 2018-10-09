from source.AuctioneerAgent import Auctioneer
from source.UtilityAgent import UtilityAgent
from source.HouseholdAgent import HouseholdAgent
from source.Electrolyzer import Electrolyzer
from source.Data import Data
from source.const import *

from mesa import Model

import logging
env_log = logging.getLogger('run_microgrid.microgrid_env')


class MicroGrid(Model):
    """ Agents are created in this environment that runs the simulation"""
    def __init__(self):
        self.step_count = 0
        self.data = Data()
        self.agents = []
        self.num_households = num_households
        self.auction_type = auction_type

        """ create the auction platform"""
        self.auction = Auctioneer(self.auction_type, self)

        """ create the utility grid"""
        self.utility = UtilityAgent(self)

        """ Create the electrolyzer (hydrogen refueling station) agent."""
        self.electrolyzer = Electrolyzer(1, self)

        """ create N agents """
        for i in range(self.num_households):
            agent = HouseholdAgent(i, self)
            self.agents.append(agent)

    def sim_step(self):
        """advance the model by one step"""

        bid_list = []
        offer_list = []

        # random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.pre_auction_step()
            # This should not be here __________
            if agent.trading_state == 'buying':
                assert agent.offer is None
                bid_list.append(agent.bid)
            elif agent.trading_state == 'supplying':
                assert agent.bid is None
                offer_list.append(agent.offer)
            # __________________________________

        self.auction.auction_round(bid_list, offer_list)
        self.update_time()

    def update_time(self):
        self.step_count += 1



