from mesa import Agent
from devices import ESS
from wallet import Wallet
from data import Data
import scipy.optimize as optimize
import numpy as np
import logging
house_log = logging.getLogger('house')


class HouseholdAgent(Agent):
    """ Agents are created by calling this function """
    def __init__(self, _unique_id, _data):
        house_log.info('agent%d created', _unique_id)
        super().__init__(_unique_id, _data)
        self.data = _data
        self.id = _unique_id
        self.load = self.data.load_profile[self.id]
        self.production = self.data.production_profile[self.id]
        self.capacity = self.data.capacity
        self.trading_state = 'passive'

        self.bid = None
        self.offer = None
        """house attributes"""
        self.ess = ESS(self)
        self.wallet = Wallet(_unique_id)

    def utility_function(self, params):
        """agent-individual utility function generates 1 quantity for 1 price"""
        # TODO: create functions that generate a demand curve (are these dynamics even needed?)

        if self.trading_state == 'buying':
            buy_allocation, price = params
            demand = - self.ess.surplus
            # TODO: what is the bidding risk? expectation of allocation increases when raising price
            utility = (demand - buy_allocation * price) ** 2 + buy_allocation * price + price * 0.008

        elif self.trading_state == 'supplying':
            sell_allocation, price = params
            surplus = self.ess.surplus
            # TODO: this does not make sense yet
            utility = (- surplus + sell_allocation*price) ** 2 - sell_allocation * price + price * 0.008
        else:
            utility = 0

        return utility

    def price_point_optimization(self):
        """optimization set-up, utility function pick-up and solver"""

        """constraints"""
        def constraint1(params):
            allocation, price = params
            return price - 0

        def constraint2(params):
            allocation, price = params
            return allocation - 0

        con1 = {'type': 'ineq', 'fun': constraint1}
        con2 = {'type': 'ineq', 'fun': constraint2}

        cons = [con1, con2]
        """initialisation values"""
        x0 = [0.1, 0.1]

        """solver using SLSQP quadratic solver"""
        print(self.trading_state)
        price_quantity_point = optimize.minimize(self.utility_function, x0, constraints=cons, method='SLSQP')
        return price_quantity_point.x

    def demand_curve(self):
        """convert utility function to a demand curve"""
        return

    def supply_curve(self):
        """convert utility function to a supply curve"""
        return

    def announce_curve(self):

        return

    def pre_auction_step(self):
        """each agent makes a step here"""
        # check state of agent, supplier or buyer
        self.ess.ess_demand_calc(self)
        if self.ess.surplus > 0:
            self.trading_state = 'supplying'
            self.offer = self.price_point_optimization()
            self.bid = None
            print(self.offer)
        elif self.ess.surplus < 0:
            self.trading_state = 'buying'
            self.bid = self.price_point_optimization()
            self.offer = None
            print(self.bid)
        else:
            self.trading_state = 'passive'
        house_log.info('house%d is %s', self.id, self.trading_state)

        # work out respective utility functions, convert into demand or supply curve

        # if something went wrong, heads-up from auctioneer

    def post_auction_step(self):
        """ after auctioneer gives clearing signal"""
        pass
