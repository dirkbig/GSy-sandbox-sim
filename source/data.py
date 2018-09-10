from source.const import num_households
import numpy as np
from source import const
import csv
import os


def csv_read_file(num_households_):
    data_dict = {}
    data_directory = "data_extended"

    i = 0
    for profile in os.listdir(data_directory):
        data_array = []
        if profile.endswith(".csv") and i < num_households_:
            with open("data_extended/" + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(row)
            print(len(data_array))
            i += 1
        data_dict[i] = data_array

    return data_dict


class Data(object):
    def __init__(self):
        """initialise data sets"""
        self.num_households = const.num_households
        data_type = "random_1_step"

        """ households need a data-set to extract various data from
            Load profile for coming interval
            Production profile for coming interval
            Devices """
        if data_type == 'random_1_step':
            self.load_profile = 1.8*np.random.rand(num_households)
            self.storage_profile = np.random.rand(num_households)
            self.production_profile = np.random.rand(num_households)

            self.capacity = np.random.rand(num_households)  # only when  household has ESS??
            
            assert len(self.load_profile) == len(self.storage_profile) == \
                len(self.production_profile) == len(self.capacity)

        elif data_type == 'custom_load_profiles':
            pass

        elif data_type == 'data_set_time_series':
            # TODO: add time series data from Stanford SMART* data-set
            self.data_dict = self.extended_data_profiles()

    def extended_data_profiles(self):
        """ loading in of load profiles """
        data_files = csv_read_file(self.num_households)
        return data_files

