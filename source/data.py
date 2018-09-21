from source.const import *
from source.data_methods import *

import numpy as np


class Data(object):
    def __init__(self):
        """initialise data sets"""
        self.num_households = num_households
        data_type = "random_1_step"  # random_1_step, custom_load_profiles, data_set_time_series
        step_length = 1440
        if data_type == 'random_1_step':
            """ check whether the market platform can complete a full run, using random numbers of simplicity
                -> do not use for testing, since input is all random, just for bug finding"""
            self.load_list = 1.8*np.random.rand(num_households)
            self.pv_gen_list = np.random.rand(num_households)
            self.electrolyzer_list = [None for electrolyzer in range(num_households)]

            self.ess_list = [[np.random.randint(0, 1) for char in range(2)] for house in range(num_households)]

            assert len(self.load_list) == len(self.ess_list) == len(self.pv_gen_list)

        elif data_type == 'custom_load_profiles':
            """ create simple (non random) test-profiles, currently also 1 step only
                -> use for testing of simply grids and hypotheses, check whether strategies are behaving"""
            self.load_list =            [0, 0, 100, 10]
            self.pv_gen_list =          [3,     None, 3, None]
            self.electrolyzer_list =    [None, None, None, None]

            self.ess_list = [[0.5, 5], [0.5, 5], [0, 5], [0, 5]]  # currently: [initial_soc, max_capacity]

            assert len(self.load_list) == len(self.ess_list) == len(self.pv_gen_list)

        elif data_type == 'data_set_time_series':
            """ run model with real data, check if the strategies are performing well, and for research results"""
            # TODO: add time series data from Stanford SMART* data-set
            self.load_dict = self.get_load_profiles()       # DONE: linked to load-profiles @ data_load_profiles
            self.pv_gen_dict = self.get_pv_gen_profiles()   # TODO: find suitable PV data set
            self.electrolyzer_list = self.get_electrolyzer_profiles()

            self.ess_list = self.get_ess_characteristics()    # TODO: currently NOT : [initial_soc, max_capacity]

            assert len(self.load_list) == len(self.ess_list) == len(self.pv_gen_list) == step_length

        if utility_presence is True:
            self.utility_pricing_profile = self.get_utility_profile()
            assert len(self.utility_pricing_profile) == step_length

        self.simulation_length_steps = len(self.load_list)

    @staticmethod
    def get_load_profiles():
        """ loading in load profiles """
        load_dict = csv_read_load_file(num_households)
        return load_dict

    @staticmethod
    def get_pv_gen_profiles():
        """ loading in load profiles """
        pv_gen_dict = {}
        for agent in range(num_households):
            pv_gen_series = np.random.rand(num_steps)
            pv_gen_dict[agent] = pv_gen_series
        return pv_gen_dict

    @staticmethod
    def get_electrolyzer_profiles():
        """ loading in load profiles """
        electrolyzer_dict = None  # TODO: None?? that is a problem...
        return electrolyzer_dict

    @staticmethod
    def get_ess_characteristics():
        """ generates ESS characteristics"""
        ess_characteristics = None  # TODO: None?? that is a problem...
        return ess_characteristics

    @staticmethod
    def get_utility_profile():
        """ loads in utility pricing profile """
        utiltiy_profile_dict = csv_read_utility_file()
        return utiltiy_profile_dict



