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

        """ Commercial PV """
        if self.data.pv_presence is True:
            pv_id = 'CommercialPv'
            self.agents[pv_id] = Pv(pv_id, self)

        self.data_collector = DataCollector()

    def sim_step(self):
        """advances the model by one step"""

        """ pre-auction round """
        print("Phase [1] Pre-Auction Round")
        pre_agent_id = []
        for agent_id in self.agents:
            self.agents[agent_id].pre_auction_round()
            pre_agent_id.append(agent_id)

        """ Utility grid treatment """
        self.agents["Utility"].append_utility_offer(self.auction.bid_list, self.auction.offer_list)
        # TODO: move this to utility agent?
        # if self.data.utility_presence is True:
        #     # Track the total amount of electricity that is wanted (bids) and that is sold (offers) [kWh]. Further set
        #     # the price of each bid, that exceeds the price the utility grid is offering electricity for, to
        #     # the offering price of the electricity grid. The same thing is done with sold energy and the price the
        #     # utility grid buys energy for.
        #     total_energy_wanted = 0
        #     total_energy_offered = 0
        #     # Get the price the utility grid sells and buys energy for [EUR/kWh].
        #     utility_buy_price = self.agents['Utility'].buy_rate_utility
        #     utility_sell_price = self.agents['Utility'].sell_rate_utility
        #     for agent_id in self.agents:
        #         # TODO: the utility should rather take info from the bid/offer list of auctioneer;
        #         # from all individual agents; thus use self.auction.bid_list and self.auction.offer_list?
        #
        #         if self.agents[agent_id].bids is not None and len(self.agents[agent_id].bids) > 0:
        #             for this_bid in self.agents[agent_id].bids:
        #                 total_energy_wanted += this_bid[1]
        #                 # if the bid price is above what utility energy costs, set it to that price[EUR/kWh].
        #                 if this_bid[0] > utility_sell_price:
        #                     this_bid[0] = utility_sell_price
        #         if self.agents[agent_id].offers is not None and len(self.agents[agent_id].offers) > 0:
        #             for this_offer in self.agents[agent_id].offers:
        #                 # TODO: PV agent creates problem here. Utility agent finds a PV offer;
        #                 # if this_offer == 0 and agent_id is 'CommercialPV' :
        #                 #     this_offer = self.agent['CommercialPV'].proxy_offer
        #                 # self.agent['CommercialPV'].offers == 0... instead of a tuple...
        #                 total_energy_offered += this_offer[1]
        #
        #                 # If the offer price is below what the utility pays for energy, set it to that price [EUR/kWh].
        #                 if this_offer[0] < utility_buy_price:
        #                     this_offer[0] = utility_buy_price
        #
        #     # Construct a bid and an offer for the utility grid that can supply or buy all energy asked for or supplied.
        #     # Bids and offers are in the format [price, quantity, self.id]
        #     self.agents['Utility'].offers = [self.agents['Utility'].sell_rate_utility, total_energy_wanted, 'Utility']
        #     self.auction.offer_list.append(self.agents['Utility'].offers)
        #
        #     # TODO: I DON'T THINK THIS IS A GOOD WAY TO DO IT. IT SHOULD BE DECOUPLED FROM THE ACTUAL AUCTION.
        #     # self.agents['Utility'].bids = [self.agents['Utility'].buy_rate_utility, total_energy_offered, 'Utility']
        #     # self.auction.bid_list.append(self.agents['Utility'].bids)
        #
        #     # self.auction.who_gets_what_dict['Utility'] = []
        #     print('Utility bid placed: {}. Utility offer placed: {}'.format(
        #         str(self.agents['Utility'].bids), str(self.agents['Utility'].offers)))

        info_string = 'Pre-auction round done for agent IDs:' + ' | {}' * len(pre_agent_id) + ' |'
        print(info_string.format(*pre_agent_id))
        print("")

        """ auction round """
        print("Phase [2] Start Auction Round")
        self.auction.auction_round()
        info_string = 'Auction round done for agent IDs:' + ' | {}' * len(pre_agent_id) + ' |'
        print(info_string.format(*pre_agent_id))
        print("")

        """ post-auction round """
        print("Phase [3] Start Post-Auction Round")
        updated_agent_id = []
        for agent_id in self.agents:
            self.agents[agent_id].post_auction_round()
            updated_agent_id.append(agent_id)

        info_string = 'Agents updated with following IDs:' + ' | {}' * len(updated_agent_id) + ' |'
        print(info_string.format(*updated_agent_id))
        print("")

        """ Alternative pricing scheme comes here """
        # TODO: alt pricing

        """ Track data """
        for agent_id in self.agents:
            self.agents[agent_id].track_data()
        self.auction.track_data()


        """ Update Time """
        self.update_time()

    def update_time(self):
        self.step_count += 1



