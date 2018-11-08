from source.auctioneer_agent import Auctioneer
from source.utility_agent import UtilityAgent
from source.household_agent import HouseholdAgent
from source.electrolyzer import Electrolyzer
from source.data import Data

from mesa import Model
import random

import logging
env_log = logging.getLogger('run_microgrid.microgrid_env')


class MicroGrid(Model):
    """ Agents are created in this environment that runs the simulation"""
    def __init__(self):

        self.data = Data()

        """ initiation """
        self.step_count = 0
        self.agents = []

        self.entities_dict = {}
        """ load in data THIS HAS TO GO FIRST"""

        """ create the auction platform"""
        self.auction = Auctioneer(self.data.auction_type, self)

        """ create the utility grid"""
        if self.data.utility_presence is True:
            self.utility = UtilityAgent(self)

        """ create N agents """
        for i in range(self.data.num_households):
            agent = HouseholdAgent(i, self)
            self.agents.append(agent)

        """ electrolyzer """
        self.agents.append(Electrolyzer(self.data.num_households, self))

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        self.utility.pre_auction_round()

        random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.pre_auction_round()

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.post_auction_round()

        """ Update the time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



