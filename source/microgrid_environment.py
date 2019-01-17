from mesa.datacollection import DataCollector
from source.auctioneer_agent import Auctioneer
from source.utility_agent import UtilityAgent
from source.household_agent import HouseholdAgent
from source.electrolyzer import Electrolyzer
from source.battery import Battery
from source.pv import Pv
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
        self.agents = {}

        """ create the auction platform"""
        self.auction = Auctioneer(self.data.pricing_rule, self)

        """ create the utility grid"""
        if self.data.utility_presence is True:
            utility_id = "Utility"
            self.agents[utility_id] = UtilityAgent(utility_id, self)

        """ create N agents """
        for house_id in range(self.data.num_households):
            self.agents[house_id] = HouseholdAgent(house_id, self)

        """ Electrolyzer """
        if self.data.electrolyzer_presence is True:
            electrolyzer_id = 'Electrolyzer'
            self.agents[electrolyzer_id] = Electrolyzer(electrolyzer_id, self)

        if self.data.battery_presence is True:
            battery_id = 'CommercialBattery'
            self.agents[battery_id] = Battery(battery_id, self)

        if self.data.pv_presence is True:
            pv_id = 'CommercialPv'
            self.agents[pv_id] = Pv(pv_id, self)

        self.data_collector = DataCollector()

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        for agent_id in self.agents:
            self.agents[agent_id].pre_auction_round()
            print(agent_id)

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        for agent_id in self.agents:
            self.agents[agent_id].post_auction_round()
            print(agent_id)

        """ Update Time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



