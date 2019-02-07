"""
In this file, new energy system profiles can be saved as an own class and loaded into the simulation.

PLAY ME: If you execute this script directly, it will show you what attributes for all configurations saved in this
file are either missing or redundant.
"""

import numpy as np


""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                        START OF PROFILES
""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

class ConfigurationUtilityEly:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.market_interval = 15  # minutes

        # time
        self.start = 0

        self.num_steps = self.num_steps = int(96*1)

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = True
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = False
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'

        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.utility_dynamical_pricing = False
        self.utility_selling_price_fix = 0.0
        self.utility_buying_price_fix = 0.0
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
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
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


class ConfigurationUtilityElyPv:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.market_interval = 15  # minutes

        # time
        self.start = 0

        self.num_steps = self.num_steps = int(96*1)

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = True
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = True
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'


        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.utility_dynamical_pricing = False
        self.utility_selling_price_fix = 0.0
        self.utility_buying_price_fix = 0.0
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
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
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


class ConfigurationUtility10prosumer:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.market_interval = 15  # minutes

        # time
        self.start = 0

        self.num_steps = int(96*30)

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = False
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = False
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'


        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.utility_dynamical_pricing = False
        self.utility_selling_price_fix = 0.25
        self.utility_buying_price_fix = 0.0
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 0
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
        self.prosumers_with_pv_and_ess = 10
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
            self.classification_array.append([True, 5, True])

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
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


class ConfigurationUtility10household:
    def __init__(self):
        """ Configuration of the grid Mixin Class"""

        """ 
            Simulation environment
        """
        self.market_interval = 15  # minutes

        # time
        self.start = 0

        self.num_steps = int(96 * 1)

        """ 
            Market structure 
        """
        # TODO: this is already defined in const.py
        self.pricing_rule = 'pac'  # or 'pab'

        """ 
            Electrolyzer
        """
        self.electrolyzer_presence = False
        self.fuel_station_load = 'ts_h2load_kg_15min_classverysmall_2015.csv'
        # Define for how many time steps in the future a forecast is supposed to be used for optimizing bidding
        # strategies of the electrolyzer.
        self.forecast_horizon = 96 * 7

        """
            Battery
        """
        self.battery_presence = False

        """
            PV commercial
        """
        self.pv_presence = False
        self.pv_commercial_profile = 'ts_pv_kWperkWinstalled_15min_2015.csv'


        """ 
            Utility 
        """
        self.utility_presence = True

        self.negative_pricing = False
        self.utility_dynamical_pricing = False
        self.utility_selling_price_fix = 0.25
        self.utility_buying_price_fix = 0.0
        self.utility_profile = 'ts_electricityintraday_EURperkWh_15min_2015.csv'

        """ 
            Households basic configuration 
        """
        self.consumers = 10
        self.prosumers_with_only_pv = 0
        self.prosumers_with_ess = 0
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
        self.num_households_with_ess = self.prosumers_with_ess + self.prosumers_with_pv_and_ess
        max_capacity_list = np.full(self.num_households_with_ess, 10)
        initial_capacity_list = np.full(self.num_households_with_ess, 9)
        self.ess_characteristics_list = []

        for battery in range(self.num_households_with_ess):
            max_capacity = max_capacity_list[battery]
            initial_soc = initial_capacity_list[battery]
            self.ess_characteristics_list.append([initial_soc, max_capacity])
        self.total_ess_capacity = sum(max_capacity_list)


""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                        END OF PROFILES
""" ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def check_profile_configuration():
    # This function checks all profiles defined here against the fields defined in "gird_config.py" and displays, if
    # different sets of variable names are used. This helps preventing errors due to a change in naming conventions and
    # shows, which default values from "grid_config.py" are used in the different profiles.

    import inspect
    import sys
    from grid_config import ConfigurationMixin

    # Get a list with all the classes in this file.
    profile_list = []
    for _, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if inspect.isclass(obj):
            this_class = globals()[obj.__name__]
            # Save a profile as an instant of the profile class to the profile list.
            profile_list.append(this_class())

    # Get a list of all variables that are defined for the profiles.
    attribute_list = []
    for this_profile in profile_list:
        attribute_list.append([attribute for attribute in this_profile.__dict__.keys() if attribute[:2] != '__'])

    # Get a list of the attributes from ConfigurationMixin in "grid_config.py", where all attributes are initiated.
    attributes_used = [attribute for attribute in ConfigurationMixin().__dict__.keys() if attribute[:2] != '__']

    # Compare each profile with the attributes that are actually used and print out which attributes are missing and
    # which are redundant.
    for i in range(len(attribute_list)):
        profile_attributes = attribute_list[i]
        attributes_redundant = profile_attributes[:]
        attributes_missing = attributes_used[:]

        for this_attribute in attributes_used:
            if this_attribute in attributes_redundant:
                attributes_redundant.remove(this_attribute)

        for this_attribute in profile_attributes:
            if this_attribute in attributes_missing:
                attributes_missing.remove(this_attribute)

        # Give a graphical output.
        print('\n+++++++++++++++++++++++++++++\nProfile {}:\nAttributes missing: {}\nRedundant attributes: {}'.format(
            type(profile_list[i]).__name__, str(attributes_missing), str(attributes_redundant)))


if __name__ == '__main__':
    # If this file is executed directly it will print out a list of attributes of each status that are missing or
    # redundant for each profile.
    check_profile_configuration()






