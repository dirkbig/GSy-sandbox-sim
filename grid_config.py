import numpy as np
from source.const import num_minutes_in_a_day

""" Grid Configuration """


class ConfigurationMixin:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.auction_type = 'pay_as_clear'
        self.num_days = 1
        self.market_interval = 15  # minutes
        self.num_steps = int(self.num_days * num_minutes_in_a_day / 15)

        """ 
            Market structure 
        """
        self.pricing_rule = 'pac'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = False
        self.cell_area = 1500
        self.n_cell = 140
        self.p = 1.5
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'

        """ 
            Utility 
        """
        self.utility_presence = True
        self.negative_pricing = False
        self.dynamical_pricing = False
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 1
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
        self.prosumers_with_pv_and_ess = 1

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
        self.household_loads_folder = 'household_load_profiles_SMART'
        self.num_households_with_consumption = self.num_households

        """ 
            PV data
        """
        self.num_pv_panels = self.prosumers_with_only_pv + self.prosumers_with_pv_and_ess
        self.pv_output_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """    
            ESS data
        """
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 1)
        initial_capacity_list = np.full(self.num_households_with_ess, 0.3)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


if __name__ == "__main__":
    config = ConfigurationMixin()
    print('fuel station load: ', config.fuel_station_load)
    print('utility prices data: ', config.utility_profile)
    print('household load dataset: ', config.household_loads_folder)
    print('total ess storage capacity: ', config.total_ess_capacity)
