import csv
import os

from source.const import selected_utility_price_profile


def csv_read_load_file(num_households_):
    data_dict = {}
    data_directory = "data_load_profiles"

    i = 0
    for profile in os.listdir(data_directory):
        data_array = []
        if profile.endswith(".csv") and i < num_households_:
            with open(data_directory + '/' + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(row)
            i += 1
        data_dict[i] = data_array

    return data_dict


def csv_read_utility_file():
    utility_data_directory = "utility_price_data"

    for profile in os.listdir(utility_data_directory):
        if profile == selected_utility_price_profile:
            data_array = []
            with open(utility_data_directory + '/' + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(row)
            del data_array[0]
            break

    utility_data_array = data_array
    return utility_data_array
