import csv
import os
import numpy as np

import logging
data_methods_log = logging.getLogger('run_microgrid.data_methods')

# WHY IS THE DIRECTORY PATH CHANGED HERE? THIS LED TO AN ERROR. WITHOUT THIS IT IS WORKING FOR ME (FROM MARLON)
# os.chdir("..")
path = "./source" + "/profiles"
#print(path)

# def csv_read_load_profile(num_households_):
#     data_dict = {}
#     data_directory = "data_load_profiles"
#


def csv_load_file(data_directory, profile):
    data_array = []
    with open(data_directory + '/' + profile) as csv_file:
        data_file = csv.reader(csv_file, delimiter=',')
        for row in data_file:
            if float(row[1]) < 0:
                row[1] = 0
            data_array.append(float(row[-1]))

    return data_array


def csv_read_load_file(num_households_with_load, household_loads_folder):
    data_list = []
    data_directory = path + '/data_load_profiles/' + household_loads_folder
    try:
        if household_loads_folder not in os.listdir(path + '/data_load_profiles'):
            data_methods_log.warning("household demand profile file '%s' not found" % household_loads_folder)
            exit()
    except FileNotFoundError:
        data_methods_log.error("File  not Found: change path")

    # Get a list with all available load profiles in the folder.
    load_profiles = os.listdir(data_directory)
    # Check if there are enough load profiles, if not, throw an error.
    if len(load_profiles) < num_households_with_load:
        raise ValueError("There are less household load profiles than there are households with loads!")
    # Only use as many load profiles as there are households. Use only files that end with .csv.
    profiles_to_use = []
    i_profile_used = 0
    while i_profile_used < num_households_with_load:
        if load_profiles[i_profile_used].endswith(".csv"):
            profiles_to_use.append(load_profiles[i_profile_used])
            i_profile_used += 1

    for profile in profiles_to_use:
        data_array = csv_load_file(data_directory, profile)
        data_list.append(data_array)

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
                    for row in data_file:
                        if float(row[1]) < 0.000001:
                            row[1] = 0
                        data_array.append(float(row[1]))

                data_list.append(data_array)
                i += 1

    return data_list


def csv_read_utility_file(selected_utility_price_profile):
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


def csv_read_pv_profile(selected_pv_load_file="ts_pv_kWperkWinstalled_15min_2015.csv"):
    pv_data_dir = path + '/pv_output_profiles'

    if selected_pv_load_file not in os.listdir(pv_data_dir):
        data_methods_log.warning("PV file '%s' not found" % selected_pv_load_file)
        exit()


    for profile in os.listdir(pv_data_dir):
        if profile == selected_pv_load_file and profile.endswith(".csv"):
            data_array = []
            with open(pv_data_dir + '/' + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(float(row[1]))
            break

    pv_load_profile = data_array
    return pv_load_profile


def csv_read_load_h2():
    # Read and return the H2 load profile for the fueling station (included in the electrolyzer class) [kg].
    data_directory = "data_timeseries"
    ts_name = "ts_h2load_classverysmall_kg_15min_2015.csv"
    data_array = []
    with open(data_directory + "/" + ts_name) as csv_file:
        data_file = csv.reader(csv_file, delimiter=',')
        for row in data_file:
            data_array.append(row)

    return data_array



def csv_read_electricity_price():
    # Read and return the intraday electricity price for the year 2015 in Germany [EUR/kWh].
    data_directory = "data_timeseries"
    ts_name = "ts_electricityintraday_EURperkWh_15min_2015.csv"
    data_array = []
    with open(data_directory + "/" + ts_name) as csv_file:
        data_file = csv.reader(csv_file, delimiter=',')
        for row in data_file:
            data_array.append(row)

    return data_array

