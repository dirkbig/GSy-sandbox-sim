from source.devices import *
from source.wallet import Wallet

from mesa import Agent
import scipy.optimize as optimize
import logging
house_log = logging.getLogger('run_microgrid.house')


class HouseholdAgent(Agent):
    """ Household agents are created through this class """
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        house_log.info('agent%d created', _unique_id)

        self.id = _unique_id
        self.model = model
        self.data = self.model.data

        """ Loading in data """
        self.load_data = self.model.data.agent_data_array[self.id][0]
        self.pv_data = self.model.data.agent_data_array[self.id][1]
        self.ess_data = self.model.data.agent_data_array[self.id][2]

        self.load_on_step = 0
        self.pv_production_on_step = 0
        self.ess_demand_on_step = 0

        """ Creation of device objects, depending is Data class assigns them """
        self.devices = {}
        self.has_load = False
        self.has_pv = False
        self.has_ess = False

        if self.load_data is not None:
            self.load = GeneralLoad(self, self.load_data)
            self.devices['GeneralLoad'] = self.load
            self.has_load = True

        if self.pv_data is not None:
            self.pv = PVPanel(self, self.pv_data)
            self.devices['PV'] = self.pv
            self.has_pv = True

        if self.ess_data is not None:
            self.ess = ESS(self, self.ess_data)
            self.devices['ESS'] = self.ess
            self.has_ess = True
            self.soc_actual = self.ess.soc_actual

        else:
            self.soc_actual = 0

        house_log.info(self.devices)

        """standard house attributes"""
        self.wallet = Wallet(_unique_id)

        """ trading """
        if self.has_ess is True:
            self.selected_strategy = 'smart_ess_strategy'
        if self.has_ess is False:
            self.selected_strategy = 'simple_strategy'

        """ overrides all strategies for a no-trade paradigm """
        self.selected_strategy = 'simple_strategy'

        self.trading_state = None
        self.bid = None
        self.offer = None
        self.energy_trade_flux = 0
        self.net_energy_in = None
        self.overflow = None
        self.deficit = None

        self.net_energy_in_simple_strategy = 0

    def utility_function(self, params):
        """agent-individual utility function generates 1 quantity for 1 price"""

        """ very naive adaptation of the use of utility functions for a smart-ESS-strategy """
        if self.trading_state == 'buying':
            # TODO: constrain by maximum willingness-to-pay?
            buy_allocation, price = params
            demand = abs(self.ess.surplus)
            utility = (demand - buy_allocation) ** 2 + buy_allocation * price * 0.001

        elif self.trading_state == 'supplying':
            # TODO: lower constrain by marginal costs and upper-constrain by utility-grid
            sell_allocation, price = params
            surplus = self.ess.surplus
            utility = (surplus - sell_allocation) ** 2 - sell_allocation * price
        else:
            utility = 0

        return utility

    def price_point_optimization(self):
        """optimization set-up, utility function pick-up and solver"""

        def constraint1(params):
            allocation, price_cons = params
            return price_cons - 0

        def constraint2(params):
            allocation, price_cons = params
            return allocation - 0

        con1 = {'type': 'ineq', 'fun': constraint1}
        con2 = {'type': 'ineq', 'fun': constraint2}

        cons = [con1, con2]
        """initialisation values"""
        x0 = [0.1, 0.1]

        """solver using SLSQP quadratic solver"""
        price_quantity_point = optimize.minimize(self.utility_function, x0, constraints=cons, method='SLSQP')
        price, quantity = price_quantity_point.x
        if quantity < 0:
            quantity = 0

        if price*quantity > self.wallet.coin_balance:
            house_log.warning('cannot afford such a bid')

        return price, quantity

    def smart_ess_strategy(self):
        """ smart ESS strategy, calls:
                -> ess_demand_calc: decides whether buying or selling, and how much;
                    -> price_point_optimization: decides on what quantity and for what price;
                        -> utility_function: governs the trade-off that the optimization optimizes.
        """
        self.ess.ess_demand_calc(self.model.step_count)

        if self.ess.surplus > 0:
            self.trading_state = 'supplying'
            """ bid approach, using utility function"""
            price, quantity = self.price_point_optimization()
            self.ess.max_in, self.ess.max_out = self.ess.get_charging_limit()
            # respects discharging limit constraints
            self.offer = [price, min(self.ess.max_out, quantity), self.id]
            self.bid = None

        elif self.ess.surplus < 0:
            self.trading_state = 'buying'
            """ offer approach using utility function """
            price, quantity = self.price_point_optimization()
            price += price + 100
            # respects charging limit constraints
            self.bid = [price, min(self.ess.max_in, quantity), self.id]
            self.offer = None
        else:
            self.trading_state = 'passive'
            self.bid = None
            self.offer = None

    def simple_strategy(self):
        """ household makes simple bid or offer depending on the net energy going in our out of the house """
        self.state_update_from_devices()

        """ Determine net energy going building up inside household """
        if self.has_ess is True:
            self.ess.ess_demand_calc(self.model.step_count)
            self.net_energy_in_simple_strategy = self.ess.surplus
        else:
            self.net_energy_in_simple_strategy = self.pv_production_on_step - abs(self.load_on_step)

        if self.net_energy_in_simple_strategy > 0:
            self.trading_state = 'supplying'
            price = 10 + self.id
            quantity = self.net_energy_in_simple_strategy
            self.offer = [price, quantity, self.id]
            self.bid = None

        elif self.net_energy_in_simple_strategy < 0:
            self.trading_state = 'buying'
            price = 20 - self.id
            quantity = abs(self.net_energy_in_simple_strategy)
            self.bid = [price, quantity, self.id]
            self.offer = None
        else:
            self.trading_state = 'passive'
            self.bid = None
            self.offer = None

        ''' PV  first supplies to ESS
                then supplies to market'''

        ''' Load first takes from ESS
                then takes from market'''

        """ should look like this """
        # marginal costs of PV()
        # supply offer (-curve) calculation

        # willingness to pay for load()
        # demand bid (-curve) calculation

        # posting of bids and offers on the market

        # wait for clearing of the market, evaluate what has been bought / sold
        # add the rest to or from the ESS

    def state_update_from_devices(self):
        """ updates the household agent on state of devices """
        current_step = self.model.step_count

        if self.has_load is True:
            self.load_on_step = self.load.get_load(current_step)

        if self.has_pv is True:
            self.pv_production_on_step = self.pv.get_generation(current_step)

    def pre_auction_round(self):
        """ each agent makes a step here, before auction step"""

        self.state_update_from_devices()
        for device in self.devices:
            self.devices[device].uniform_call_to_device(self.model.step_count)

        """ 
            STRATEGIES 
            how to come up with price-quantity points on the auction platform 
        """
        if self.has_ess is True and self.selected_strategy == 'smart_ess_strategy':
            self.smart_ess_strategy()

        elif self.selected_strategy == 'simple_strategy':
            self.simple_strategy()

        elif self.selected_strategy == 'no_trade':
            self.offer = None
            self.bid = None

        self.announce_bid_and_offers()

    def post_auction_round(self):
        """ after auctioneer gives clearing signal and """

        self.energy_trade_flux = sum(self.model.auction.who_gets_what_dict[self.id])
        self.net_energy_in = self.pv_production_on_step + self.load_on_step + self.energy_trade_flux
        """ update ESS and unmatched loads """
        if self.has_ess is True:
            self.overflow, self.deficit = self.ess.update_ess_state(self.net_energy_in)
        else:
            if self.net_energy_in > 0:
                self.overflow = abs(self.net_energy_in)
                self.deficit = 0
            else:
                self.overflow = 0
                self.deficit = abs(self.net_energy_in)

        """ data logging """
        self.data.overflow_over_time[self.id][self.model.step_count] = self.overflow
        self.data.deficit_over_time[self.id][self.model.step_count] = self.deficit

    def announce_bid_and_offers(self):
        """ announces bid to auction agent by appending to bid list """
        house_log.info('house%d is %s', self.id, self.trading_state)

        if self.trading_state == 'supplying':
            self.model.auction.offer_list.append(self.offer)

        elif self.trading_state == 'buying':
            self.model.auction.bid_list.append(self.bid)


