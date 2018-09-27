import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
sns.set()


def clearing_snapshot(clearing_quantity, clearing_price, sorted_x_y_y_pairs_list):
    # TODO: export these demand/supply curves
    x_quantities = []
    y_bid_prices = []
    y_offer_prices = []

    for i in range(len(sorted_x_y_y_pairs_list)):
        x_quantities.append(sorted_x_y_y_pairs_list[i][0])
        y_bid_prices.append(sorted_x_y_y_pairs_list[i][1])
        y_offer_prices.append(sorted_x_y_y_pairs_list[i][2])

    fig, ax = plt.subplots()

    ax.step(x_quantities, y_bid_prices, label='bids')
    ax.step(x_quantities, y_offer_prices, label='offers')
    if clearing_quantity is not None:
        ax.axvline(x=clearing_quantity, color='black', linestyle='--')
        ax.axhline(y=clearing_price, color='black', linestyle='--')
    ax.legend()
    ax.set(xlabel='quantity', ylabel='price',
           title='clearing markets aggregate demand and supply blocks')
    plt.show()

    # TODO: somehow update the plot every plot, look into:
    # https://stackoverflow.com/questions/46001645/how-to-make-a-progresing-plot-in-matplotlib


def plot_avg_load_profile(num_steps, load_array):
    print(load_array)
    steps = range(num_steps)
    fig, ax = plt.subplots()
    # for agent in range(len(load_array)):
    #     ax.plot(steps, load_array[agent])

    avg_load = np.ndarray.sum(np.array(load_array), axis=0) # / len(load_array)

    ax.plot(steps, avg_load)
    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='avg Load')


def plot_avg_pv_profile(num_steps, pv_array):

    steps = range(num_steps)
    fig, ax = plt.subplots()
    # for pv in range(len(pv_array)):
    #     ax.plot(steps, pv_array[pv])
    # ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
    #        title='PV output')

    avg_pv_output = np.sum(pv_array, axis=0)/len(pv_array)

    ax.plot(steps, avg_pv_output)
    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='avg PV output')


def plot_fuel_station_profile(num_steps, fuel_station_profile):

    steps = range(num_steps)
    fig, ax = plt.subplots()
    ax.plot(steps, fuel_station_profile)
    ax.set(xlabel='sim steps', ylabel='H2 [kg] / step-interval',
           title='Load fuel station ')


def show():
    plt.show()