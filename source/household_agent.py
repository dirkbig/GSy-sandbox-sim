from mesa import Agent
from source.devices import *
from source.wallet import Wallet
import scipy.optimize as optimize
import logging
house_log = logging.getLogger('house')


class HouseholdAgent(Agent):
    """ Agents are created by calling this function """
    def __init__(self, _unique_id, _data):
        house_log.info('agent%d created', _unique_id)
        super().__init__(_unique_id, _data)
        self.data = _data
        self.id = _unique_id

        """ Devices """
        self.load = self.data.load_profile[self.id]
        # TODO: add custom (simple) load profile
        # TODO: add SMART* data-set load profile

        self.production = self.data.production_profile[self.id]
        # TODO: link this directly to a PV model / SMART* data-set


        """standard house attributes"""
        self.wallet = Wallet(_unique_id)
        """set-up dependant house attributes"""
        self.capacity = self.data.capacity
        self.ess = ESS(self)
        # TODO: make a house setup configurable, goal is to have a diverse grid configuration
        # For example:
        # self.load = GeneralLoad(self)
        # self.electrolyzer = Electrolyzer(self)
        # self.PV = PVPanel(self)

        """ Trading state"""
        self.trading_state = 'passive'
        self.bid = None
        self.offer = None
        self.sold_energy = None
        self.bought_energy = None



    def utility_function(self, params):
        """agent-individual utility function generates 1 quantity for 1 price"""
        # TODO: create functions that generate a demand curve (are these dynamics even needed?)
        if self.trading_state == 'buying':
            buy_allocation, price = params
            demand = - self.ess.surplus
            # TODO: what is the bidding risk? expectation of allocation increases when raising price
            utility = (demand - buy_allocation * price) ** 2 + buy_allocation * price + price * 0.005

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
        price_quantity_point = optimize.minimize(self.utility_function, x0, constraints=cons, method='SLSQP')
        price, quantity = price_quantity_point.x

        if price*quantity > self.wallet.coin_balance:
            house_log.warning('cannot afford such a bid')

        return price, quantity

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
            price, quantity = self.price_point_optimization()
            self.offer = [price, quantity, self.id]
            self.bid = None
        elif self.ess.surplus < 0:
            self.trading_state = 'buying'
            price, quantity = self.price_point_optimization()
            self.bid = [price, quantity, self.id]
            self.offer = None
        else:
            self.trading_state = 'passive'
        house_log.info('house%d is %s', self.id, self.trading_state)

        # work out respective utility functions, convert into demand or supply curve

        # if something went wrong, heads-up from auctioneer

    def post_auction_step(self):
        """ after auctioneer gives clearing signal"""
        pass
