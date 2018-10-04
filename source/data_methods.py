import csv
import os


def csv_read_load_profile(num_households_):
    data_dict = {}
    data_directory = "data_load_profiles"

    i = 0
    for profile in os.listdir(data_directory):
        data_array = []
        if profile.endswith(".csv") and i < num_households_:
            with open(data_directory + "/" + profile) as csv_file:
                data_file = csv.reader(csv_file, delimiter=',')
                for row in data_file:
                    data_array.append(row)
            # print(len(data_array))
            i += 1
        data_dict[i] = data_array

    return data_dict


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


def csv_read_pv_profile():
    # Read and return a PV generation profile for Berlin in 2015 [kW/kW_peak].
    data_directory = "data_timeseries"
    ts_name = "ts_pv_kWperkWinstalled_15min_2015.csv"
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

