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
        # Track the total amount of electricity that is wanted (bids) and that is sold (offers) [kWh]
        total_energy_wanted = 0
        total_energy_offered = 0
        pre_agent_id = []
        for agent_id in self.agents:
            self.agents[agent_id].pre_auction_round()
            pre_agent_id.append(agent_id)
            if self.agents[agent_id].bids is not None and len(self.agents[agent_id].bids) > 0:
                total_energy_wanted += self.agents[agent_id].bids[0][1]
            if self.agents[agent_id].offers is not None and len(self.agents[agent_id].offers) > 0:
                total_energy_offered += self.agents[agent_id].offers[0][1]

        if self.data.utility_presence is True:
            # Construct a bid and an offer for the utility grid that can supply or buy all energy asked for or supplied.
            # Bids and offers are in the format [price, quantity, self.id]
            self.agents['Utility'].offers = [self.agents['Utility'].sell_rate_utility, total_energy_wanted, 'Utility']
            self.auction.offer_list.append(self.agents['Utility'].offers)
            self.agents['Utility'].bids = [self.agents['Utility'].buy_rate_utility, total_energy_offered, 'Utility']
            self.auction.bid_list.append(self.agents['Utility'].bids)
            # self.auction.who_gets_what_dict['Utility'] = []
            print('Utility bid placed: {}. Utility offer placed: {}'.format(
                str(self.agents['Utility'].bids), str(self.agents['Utility'].offers)))

        info_string = 'Pre-auction round done for agent IDs:' + ' | {}' * len(pre_agent_id) + ' |'
        print(info_string.format(*pre_agent_id))

        """ auction round """
        self.auction.auction_round()

        """ post-auction round """
        updated_agent_id = []
        for agent_id in self.agents:
            self.agents[agent_id].post_auction_round()
            updated_agent_id.append(agent_id)

        info_string = 'Agents updated with following IDs:' + ' | {}' * len(updated_agent_id) + ' |'
        print(info_string.format(*updated_agent_id))

        """ Update Time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



