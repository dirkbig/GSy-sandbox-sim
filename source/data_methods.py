import csv
import os
import numpy as np

import logging
data_methods_log = logging.getLogger('data_methods')

path = "/Users/dirkvandenbiggelaar/gsy/pac/profiles"


def csv_read_load_file(num_households_with_load, household_loads_folder):
    data_list = []
    data_directory = path + '/data_load_profiles/' + household_loads_folder

    if household_loads_folder not in os.listdir(path + '/data_load_profiles'):
        data_methods_log.warning("pv file '%s' not found" % household_loads_folder)
        exit()

    i = 0
    for profile in os.listdir(data_directory):
        data_array = []
        if profile.endswith(".csv"):
            with open(data_directory + '/' + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    if float(row[1]) < 0:
                        row[1] = 0
                    data_array.append(float(row[-1]))
        data_list.append(data_array)
        i += 1
        if i == num_households_with_load:
            break


    return data_list


def csv_read_pv_output_file(num_pv_panels, pv_output_profile):
    data_list = []
    data_directory = path + '/pv_output_profiles'

    if pv_output_profile not in os.listdir(data_directory):
        data_methods_log.warning("pv file '%s' not found" % pv_output_profile)
        exit()

    i = 0
    while i < num_pv_panels:
        for profile in os.listdir(data_directory):
            data_array = []
            if profile == pv_output_profile and profile.endswith(".csv"):
                with open(data_directory + '/' + profile) as csv_file:
                    data_file = csv.reader(csv_file, delimiter=',')
                    row_i = 0
                    for row in data_file:
                        if float(row[1]) < 0.000001:
                            row[1] = 0
                        data_array.append(float(row[1]))
                        row_i += 1
                        if row_i >= 96:
                            break

                data_list.append(data_array)
                i += 1

    return data_list


def csv_read_utility_file(selected_utility_price_profile, num_steps):
    utility_data_dir = path + "/utility_price_profiles"

    if selected_utility_price_profile not in os.listdir(utility_data_dir):
        data_methods_log.warning("utility file '%s' not found" % selected_utility_price_profile)
        exit()

    for profile in os.listdir(utility_data_dir):
        if profile == selected_utility_price_profile and profile.endswith(".csv"):
            data_array = []
            with open(utility_data_dir + '/' + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                row_i = 0
                for row in data_file:
                    price = float(row[-1])
                    data_array.append(price)
                    row_i += 1
                    if row_i >= num_steps:
                        break

    utility_data_array = data_array
    return utility_data_array


def csv_read_electrolyzer_profile(selected_electrolyzer_load_file):
    electrolyzer_data_dir = path + '/electrolyzer_load_profiles'

    if selected_electrolyzer_load_file not in os.listdir(electrolyzer_data_dir):
        data_methods_log.warning("electrolyzer file '%s' not found" % selected_electrolyzer_load_file)
        exit()

    for profile in os.listdir(electrolyzer_data_dir):
        if profile == selected_electrolyzer_load_file and profile.endswith(".csv"):
            data_array = []
            with open(electrolyzer_data_dir + '/' + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(float(row[1]))
            break

    electrolyzer_load_profile = data_array
    return electrolyzer_load_profile


