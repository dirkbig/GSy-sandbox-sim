from mesa.datacollection import DataCollector
from source.auctioneer_agent import Auctioneer
from source.utility_agent import UtilityAgent
from source.household_agent import HouseholdAgent
from source.electrolyzer import Electrolyzer
from source.battery import Battery
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
        self.electrolyzer = None
        self.utility = None

        self.entities_dict = {}

        """ create the auction platform"""
        self.auction = Auctioneer(self.data.pricing_rule, self)

        """ create the utility grid"""
        if self.data.utility_presence is True:
            self.utility = UtilityAgent(self)

        """ create N agents """
        for i in range(self.data.num_households):
            agent = HouseholdAgent(i, self)

        id = i

        """ electrolyzer """
        i = "electrolyzer"
        if self.data.electrolyzer_presence is True:
            self.agents.append(Electrolyzer(id, self))
            id += 1

        if self.data.battery_presence is True:
            self.agents.append(Battery(id, self))
            id += 1

        self.data_collector = DataCollector()

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        if self.utility is not None:
            self.utility.pre_auction_round()

        random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.pre_auction_round()

        if self.utility is not None:
            self.utility.pre_auction_round()

        if self.electrolyzer is not None:
            self.electrolyzer.pre_auction_round()

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        for agent in self.agents[:]:
            agent.post_auction_round()

        if self.utility is not None:
            self.utility.post_auction_round()

        if self.electrolyzer is not None:
            self.electrolyzer.post_auction_round()

        """ Update the time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



