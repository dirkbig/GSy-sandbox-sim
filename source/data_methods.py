import csv
import os


def csv_read_file(num_households_):
    data_dict = {}
    data_directory = "data_load_profiles"

    i = 0
    for profile in os.listdir(data_directory):
        data_array = []
        if profile.endswith(".csv") and i < num_households_:
            with open("data_load_profiles/" + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(row)
            print(len(data_array))
            i += 1
        data_dict[i] = data_array

    return data_dict
