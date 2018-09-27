from source.auctioneer_agent import Auctioneer
from source.utility_agent import UtilityAgent
from source.household_agent import HouseholdAgent
from source.electrolyzer import Electrolyzer
from source.data import Data
from source.const import *

from mesa import Model
import random

import logging
env_log = logging.getLogger('microgrid_env')


class MicroGrid(Model):
    """ Agents are created in this environment that runs the simulation"""
    def __init__(self):

        self.data = Data()

        """ initiation """
        self.step_count = 0
        self.agents = []
        self.electrolyzer = None
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
        self.electrolyzer = Electrolyzer(i, self)

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.pre_auction_round()
        self.electrolyzer.pre_auction_round()

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.post_auction_round()
        self.electrolyzer.post_auction_round()

        self.update_time()

    def update_time(self):
        self.step_count += 1



