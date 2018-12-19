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
    def __init__(self,  run_configuration=None):

        self.data = Data(run_configuration)

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
        last_id = -1
        for i in range(self.data.num_households):
            self.agents.append(HouseholdAgent(i, self))
            # Save the id number for further agents.
            last_id = i

        """ electrolyzer """
        if self.data.electrolyzer_presence is True:
            last_id += 1
            self.agents.append(Electrolyzer(last_id, self))

        if self.data.battery_presence is True:
            last_id += 1
            self.agents.append(Battery(last_id, self))

        self.data_collector = DataCollector()

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        random.shuffle(self.agents)
        for agent in self.agents[:]:
            agent.pre_auction_round()

        if self.utility is not None:
            self.utility.pre_auction_round()

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        for agent in self.agents[:]:
            agent.post_auction_round()

        if self.utility is not None:
            self.utility.post_auction_round()

        """ Update the time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



