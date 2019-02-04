'''
This function takes the index of a household as input and evaluates it's behavior in the last simulation.
'''

from eval_result.load_result import get_result
from source.data_methods import csv_load_file
import numpy as np
import matplotlib.pyplot as plt


def eval_household(id):

    # Load the last result data. Individual bids are given in the format
    # [id_seller, id_buyer, quantity [kWh], price*quantity [EUR]].
    result_data = get_result()
    n_step = len(result_data)
    # Energy quantities bought or sold [kWh].
    energy_bought = np.zeros(n_step)
    energy_sold = np.zeros(n_step)
    # Energy price [EUR/kWh].
    energy_price = np.zeros(n_step)
    # Cycle through the result and save each bidding and offering.

    for i in range(n_step):
        this_result = result_data[i]
        if len(this_result) > 0:
            # Case: There were at least one trade this step.
            for this_trade in this_result:
                if this_trade[0] == id:
                    # Case: This household sold energy.
                    energy_sold[i] += this_trade[2]
                    energy_price[i] = this_trade[3] / this_trade[2]
                elif this_trade[1] == id:
                    # Case: This household bought energy.
                    energy_bought[i] += this_trade[2]
                    energy_price[i] = this_trade[3] / this_trade[2]


    # Load the load data of this household [kWh].
    data_directory = '../source/profiles/data_load_profiles/household_load_profiles_htw'
    # Get the name of the profile which ends with three numbers, so for id 5 the name would be
    # ts_household_kWh_15min_2015_h005.
    profile_name = 'ts_household_kWh_15min_2015_h' + str(int(id)).zfill(3) + '.csv'
    energy_load = csv_load_file(data_directory, profile_name)
    energy_load = energy_load[:n_step]

    # Plot all the data.
    steps = range(n_step)
    fig, ax = plt.subplots()
    ax.step(steps, energy_bought, label='Energy bought')
    ax.step(steps, energy_sold, label='Energy sold')
    ax.step(steps, energy_load, label='Energy demand')
    ax.set(xlabel='sim steps', ylabel='Energy [kWh]')
    ax.legend(loc='upper center', shadow=True, fontsize='x-large')
    plt.show()

    print(result_data)


if __name__ == '__main__':
    eval_household('5')



