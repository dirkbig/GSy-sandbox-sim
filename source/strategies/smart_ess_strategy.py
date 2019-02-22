import scipy.optimize as optimize
import logging
import numpy as np

strategy_log = logging.getLogger('run_microgrid.house')


def smart_ess_strategy(self):
    """ smart ESS strategy, calls:
            get_charging_limit: checks what is the max (dis)charging rate
            ess_demand_calc: decides whether buying or selling, and how much;
            price_point_optimization: decides on what quantity and for what price;
            utility_function: governs the trade-off that the optimization optimizes.
    """

    """ Determine Volume """
    self.ess.max_in, self.ess.max_out = self.ess.get_charging_limit()
    self.ess.ess_demand_calc(self.model.step_count)
    discrete_offer_list = []
    discrete_bid_list = []
    # price for which utility sells energy at this interval.
    if self.data.utility_presence is True:
        """ instead of making the utility set the upper limit, some other method is needed. 
        For now, it suffices to set an arbitrary value... e.g. 30 ct/kWh """
        utility_price = self.model.agents['Utility'].sell_rate_utility
    else:
        utility_price = 30

    max_entries_to_market = 4

    if self.ess.surplus > 0:
        self.trading_state = 'supplying'
        self.offers = []

        # respects discharging limit constraints
        offer_volume = min(self.ess.surplus, self.ess.max_out)

        if self.bidding_method is "utility_function" and offer_volume > 0:
            """ Determine Price """
            discrete_offer_list = price_point_optimization(self)

        elif self.bidding_method is "price_curve" and offer_volume > 0:
            """ Discrete offer curve: multiple bids """
            base = 0
            number_of_offers = max(max_entries_to_market, int(self.ess.surplus))
            assert self.ess.surplus > 0
            discrete_offer_list = battery_price_curve(self, utility_price, base, offer_volume,  number_of_offers)

        for offer in discrete_offer_list:
            if offer[0] is not 0:
                self.offers.append([offer[0], offer[1], self.id])
        self.bids = None

    elif self.ess.surplus < 0:
        self.trading_state = 'buying'
        bidding_volume = abs(self.ess.surplus)
        self.bids = []

        """ make sure ess buys at least essential demand"""
        # if reserves (soc_actual) is lower that the essential demand, then append this demand to bid curve as
        # inflexible, thus at price taking rates (at utility prices)
        essential_demand = max(0, self.ess.soc_essential - self.ess.soc_actual)
        soc_leftover_space = self.ess.max_capacity - essential_demand - self.ess.soc_actual
        margin = 0.00001
        assert self.ess.max_capacity - margin < self.ess.soc_actual + essential_demand + soc_leftover_space < \
               self.ess.max_capacity + margin

        if essential_demand > 0 and self.data.utility_presence is True:
            print("essential_demand", essential_demand)
            self.bids.append([utility_price, essential_demand, self.id])
            bidding_volume -= essential_demand

        elif essential_demand > 0 and self.data.utility_presence is False:
            # price taking at utility prices won't be a guarantee, thus effect set to zero this way.
            essential_demand = 0

        possible_in = bidding_volume + self.generation_on_step
        max_possible_in = self.ess.max_capacity - self.ess.soc_actual + abs(self.load_on_step)

        try:
            assert possible_in <= max_possible_in + margin
        except AssertionError:
            print("overshoot error", abs(possible_in - max_possible_in))
            exit("fix this")

        if self.bidding_method is "utility_function" and bidding_volume > 0:
            """ bid approach, using utility function: only 1 bid """
            discrete_bid_list = price_point_optimization(self)

        elif self.bidding_method is "price_curve" and bidding_volume > 0:
            """ bid approach, using discrete offer curve: multiple bids
                constrained by lower and higher bounds"""
            base = 0
            # a bid for every kWh seems, fair, with a certain maximum amount to bids)
            number_of_bids = max(max_entries_to_market, bidding_volume)
            try:
                assert soc_leftover_space >= 0
            except AssertionError:
                exit("AssertionError: soc_leftover_space >= 0")

            discrete_bid_list = battery_price_curve(self, utility_price, base, bidding_volume, number_of_bids)

        # first bid is the essential demand, bought in at utility price
        if essential_demand > 0:
            self.bids.append([utility_price, essential_demand, self.id])

        for bid in discrete_bid_list:
            if bid[0] is not 0:
                self.bids.append([bid[0], bid[1], self.id])
        self.offers = None

    else:
        self.trading_state = 'passive'
        self.bids = None
        self.offers = None


def price_point_optimization(self):
    """optimization set-up, utility function pick-up and solver"""

    def utility_function(params):
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
    price_quantity_point = optimize.minimize(utility_function, x0, constraints=cons, method='SLSQP')
    price, quantity = price_quantity_point.x
    if quantity < 0:
        quantity = 0

    if price*quantity > self.wallet.coin_balance:
        strategy_log.warning('cannot afford such a bid')

    return [[price, quantity]]


def battery_price_curve(self, mmr, base, trade_volume, number_of_bids):

    try:
        assert trade_volume > 0 and number_of_bids > 0
    except AssertionError:
        print(trade_volume)
        print(number_of_bids)
        exit("Operation with zero")

    increment = trade_volume/number_of_bids
    bid_range = np.arange(0, trade_volume, increment)

    # risk parameter in case of selling:
    #   high: risk averse, battery really wants to sell and not be a price pusher
    #   low: greedy, battery wants to be a price pusher.
    risk_parameter = 4  # for now. Could be depending on personal behaviour or trade volume.
    # clamp between 0.2 and 4, which is kind of the limits for such a parameter.
    clamp = lambda value, minn, maxn: max(min(maxn, value), minn)
    risk_parameter = clamp(risk_parameter, 0.1, 10)

    discrete_bid_curve = []
    volume_prev = 0
    volume_total = 0
    for volume in bid_range:
        price = None
        if self.trading_state is 'supplying':
            price = (mmr - base)/trade_volume**risk_parameter * volume**risk_parameter + base
        elif self.trading_state is 'buying':
            price = mmr - (mmr - base)/trade_volume**risk_parameter * volume**risk_parameter + 0.01

        # assert price <= mmr
        discrete_bid_curve.append([price, volume - volume_prev])
        volume_prev = volume

    return discrete_bid_curve
