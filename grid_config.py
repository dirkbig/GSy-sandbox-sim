import numpy as np
import source.const as const

import logging
config_log = logging.getLogger('grid_config.constants')

""" Grid Configuration """


class ConfigurationMixin:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""
        self.sim_start = 0
        self.market_interval = 15  # minutes
        num_days = 4
        self.num_steps = int(24 * 60 * num_days / self.market_interval)

        """ 
            Market structure 
        """
        self.pricing_rule = 'pab'  # 'pac', 'pab' or 'mcafee'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = False
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 0
        # Define the price distribution for stepwise bidding [EUR/kWh].
        self.ely_stepwise_bid_price = [0.2, 0.16, 0.12, 0.08]

        """
            Commercial battery
        """
        self.battery_presence = False

        """
            Commercial PV 
        """
        self.pv_presence = True
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """ 
            Utility 
        """
        # Define if a utility grid should be part of the energy system
        self.utility_presence = True
        # Define if the utility price should be loaded
        self.utility_dynamical_pricing = False
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'
        # Define if negatives prices are possible. If not, at time steps where the time series price plus the fixed
        # price is negative, it is set to 0 EUR/kWh instead.
        self.negative_pricing = False
        # Define a fixed price for electricity from the utility grid. If a time series with an electricity price is
        # loaded, the fixed price is added on top of that price from the time series [EUR/kWh].
        self.utility_selling_price_fix = 30.0
        self.utility_buying_price_fix = 30.0

        # alternative pricing scheme for rest-production.
        self.fit_pricing = False

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 1
        self.prosumers_with_ess = 1
        self.prosumers_with_pv_and_ess = 0
        self.num_households = self.consumers + self.prosumers_with_only_pv + self.prosumers_with_ess + \
            self.prosumers_with_pv_and_ess
        self.classification_array = []

        """ consumers"""
        for agent in range(self.consumers):
            self.classification_array.append([True, False, False])

        """ prosumers with only PV """
        for agent in range(self.prosumers_with_only_pv):
            self.classification_array.append([True, True, False])

        """ prosumers with only ESS"""
        for agent in range(self.prosumers_with_ess):
            self.classification_array.append([True, False, True])

        """ prosumers with both PV and ESS"""
        for agent in range(self.prosumers_with_pv_and_ess):
            self.classification_array.append([True, True, True])

        """ 
            Load data
        """
        self.household_loads_folder = 'household_load_profiles_htw'
        self.num_households_with_consumption = self.num_households

        """ 
            PV data
        """
        self.num_pv_panels = self.prosumers_with_only_pv + self.prosumers_with_pv_and_ess
        self.pv_output_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """    
            ESS data
        """

        """ ESS constants"""
        self.horizon = 24
        self.constraints_setting = "off"  # "off" or "on"
        self.battery_aging = "off"  # "off" or "on"

        if self.constraints_setting == 'off':
            config_log.warning("Physical battery constraints are not active")

        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 7)
        initial_capacity_list = np.full(self.num_households_with_ess, 0)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)

    def update_config(self, new_self):
        # Here the default config values can be overwritten by another config object.
        # Object attributes from object obj_name can be fetched by obj(obj_name).
        # Next to attribute data, other data is fetched as well, which begins with underscores.
        # Each attribute of new_self overwrites the field with name x from the original object.
        [setattr(self, x, getattr(new_self, x)) for x in dir(new_self) if not x.startswith('__')]


if __name__ == "__main__":
    config = ConfigurationMixin()
    print('fuel station load: ', config.fuel_station_load)
    print('utility prices data: ', config.utility_profile)
    print('household load dataset: ', config.household_loads_folder)
    print('total ess storage capacity: ', config.total_ess_capacity)
