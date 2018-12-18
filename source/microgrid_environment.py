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
        self.agents = {}

        self.entities_dict = {}

        """ create the auction platform"""
        self.auction = Auctioneer(self.data.pricing_rule, self)

        """ create the utility grid"""
        if self.data.utility_presence is True:
            # self.utility = UtilityAgent(self)
            utility_id = "Utility"
            self.agents[utility_id] = UtilityAgent(utility_id, self)

        """ create N agents """
        for id in range(self.data.num_households):
            # self.agents.append(HouseholdAgent(i, self))
            house_id = "House_" + str(id)
            self.agents[house_id] = HouseholdAgent(id, self)

        """ Electrolyzer """
        if self.data.electrolyzer_presence is True:
            electrolyzer_id = 'Electrolyzer'
            # self.agents.append(Electrolyzer(id, self))
            self.agents[electrolyzer_id] = Electrolyzer(electrolyzer_id, self)

        if self.data.battery_presence is True:
            battery_id = 'CommercialBattery'
            # self.agents.append(Battery(id, self))
            self.agents[battery_id] = Battery(battery_id, self)

        self.data_collector = DataCollector()

        print(self.agents)

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        # if self.data.utility_presence is True:
        #     self.agents["Utility"].pre_auction_round()

        for agent_id in self.agents:
            self.agents[agent_id].pre_auction_round()
            print(agent_id)

        # if self.data.electrolyzer_presence is True:
        #     self.agents['Electrolyzer'].pre_auction_round()

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        for agent_id in self.agents:
            self.agents[agent_id].post_auction_round()
            print(agent_id)

        """ Update the time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



