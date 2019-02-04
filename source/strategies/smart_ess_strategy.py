import scipy.optimize as optimize
import logging
import numpy as np

strategy_log = logging.getLogger('run_microgrid.house')


def smart_ess_strategy(self):
    """ smart ESS strategy, calls:
            -> ess_demand_calc: decides whether buying or selling, and how much;
                -> price_point_optimization: decides on what quantity and for what price;
                    -> utility_function: governs the trade-off that the optimization optimizes.
    """

    """ Determine Volume """
    self.ess.max_in, self.ess.max_out = self.ess.get_charging_limit()
    self.ess.ess_demand_calc(self.model.step_count)

    if self.ess.surplus > 0:
        self.trading_state = 'supplying'
        # respects discharging limit constraints
        self.ess.surplus = min(self.ess.surplus, self.ess.max_out)

        if self.bidding_method is "utility_function":
            """ Determine Price """
            discrete_offer_list = price_point_optimization(self)

        elif self.bidding_method is "price_curve":

            """ bid approach, using discrete offer curve: multiple bids
                constrained by lower and higher bounds"""
            mmr = self.model.auction.utility_market_maker_rate
            base = 0
            number_of_offers = max(3, int(self.ess.surplus))
            discrete_offer_list = battery_price_curve(self, mmr, base, self.ess.surplus, number_of_offers)

        self.offers = []
        for offer in discrete_offer_list:
            if offer[0] is not 0:
                self.offers.append([offer[0], offer[1], self.id])
        self.bids = None

    elif self.ess.surplus < 0:
        self.trading_state = 'buying'

        if self.bidding_method is "utility_function":
            """ bid approach, using utility function: only 1 bid """
            discrete_bid_list = price_point_optimization(self)

        elif self.bidding_method is "price_curve":
            """ bid approach, using discrete offer curve: multiple bids
                constrained by lower and higher bounds"""
            mmr = self.model.auction.utility_market_maker_rate
            base = 0
            # a bid for every kWh seems, fair, and 5 as a minimum number of bids)
            number_of_bids = max(5, int(self.ess.surplus))

            discrete_bid_list = battery_price_curve(self, mmr, base, abs(self.ess.surplus), number_of_bids)
            # HOTFIX - RAISE THE MONEY THAT IS PAYED FOR ELECTRICITY BY A CERTAIN FACTOR
            for i in range(len(discrete_bid_list)):
                discrete_bid_list[i][0] *= 1.3

        self.bids = []
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


def battery_price_curve(self, mmr, base, total_trade_volume, number_of_bids):

    increment = total_trade_volume/number_of_bids
    bid_range = np.arange(0, total_trade_volume, increment)

    # risk parameter in case of selling:
    #   high: risk averse, battery really wants to sell and not be a price pusher
    #   low: greedy, battery wants to be a price pusher.
    risk_parameter = 2  # for now. Could be depending on personal behaviour or trade volume.
    # clamp between 0.2 and 4, which is kind of the limits for such a parameter.
    clamp = lambda value, minn, maxn: max(min(maxn, value), minn)
    risk_parameter = clamp(risk_parameter, 0.2, 4)

    discrete_bid_curve = []
    volume_prev = 0
    for volume in bid_range:
        if self.trading_state is 'supplying':
            price = (mmr - base)/total_trade_volume**risk_parameter * volume**risk_parameter + base
        elif self.trading_state is 'buying':
            price = mmr - (mmr - base)/total_trade_volume**risk_parameter * volume**risk_parameter

        assert price <= mmr
        discrete_bid_curve.append([price, volume - volume_prev])
        volume_prev = volume

    return discrete_bid_curve
