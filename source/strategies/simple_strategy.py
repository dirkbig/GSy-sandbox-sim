import logging

strategy_log = logging.getLogger('run_microgrid.house')


def simple_strategy(self):
    """ household makes simple bid or offer depending on the net energy going in our out of the house """

    # self.state_update_from_devices()

    """ Determine Volume """
    if self.has_ess is True:
        # this is only reached when the smart-ess-strategy is overridden at init
        self.ess.ess_demand_calc(self.model.step_count)
        self.ess.surplus = self.soc_actual
        self.net_energy_in_simple_strategy = self.ess.surplus
    else:
        self.net_energy_in_simple_strategy = self.generation_on_step - abs(self.load_on_step)

    """ Determine Price """
    if self.net_energy_in_simple_strategy > 0:
        self.trading_state = 'supplying'
        price = 0  # marginal cost of zero for a PV?
        quantity = self.net_energy_in_simple_strategy
        self.offers = [[price, quantity, self.id]]
        self.bids = None

    elif self.net_energy_in_simple_strategy < 0:
        self.trading_state = 'buying'
        price = self.model.agents["Utility"].price_sell
        quantity = abs(self.net_energy_in_simple_strategy)
        self.bids = [[price, quantity, self.id]]
        self.offers = None

    else:
        self.trading_state = 'passive'
        self.bids = None
        self.offers = None

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
