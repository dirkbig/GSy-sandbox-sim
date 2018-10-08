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

    steps = range(num_steps)
    fig, ax = plt.subplots()
    for agent in range(len(load_array)):
        # ax.plot(steps, load_array[agent], alpha=0.1)
        pass
    avg_load = np.ndarray.sum(np.array(load_array), axis=0) / len(load_array)

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


def total_generation_vs_consumption(num_steps, pv_array, load_array):

    steps = range(num_steps)
    total_load = np.ndarray.sum(np.array(load_array), axis=0) / len(load_array)
    total_pv_output = np.sum(pv_array, axis=0)/ len(pv_array)

    fig, ax = plt.subplots()
    ax.plot(steps, total_load, label='total load')
    ax.plot(steps, total_pv_output, label='total pv')

    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='Total generation vs. consumption')

    ax.legend(loc='lower right', bbox_to_anchor=(1, 1), ncol=3, fontsize=8)


def soc_over_time(num_steps, soc_per_agent_over_time_array):

    """ throw away all rows filled with zero """
    # TODO: delete rows that are all zero, only non-zero rows are relevant

    steps = range(num_steps)
    fig, ax = plt.subplots()
    for ess in range(len(soc_per_agent_over_time_array)):
        ax.plot(steps, soc_per_agent_over_time_array[ess])
    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='ESS soc')


def households_deficit_overflow(num_steps, deficit_over_time, overflow_over_time):


    steps = range(num_steps)
    fig, ax = plt.subplots()
    """ overflows """
    # for ess in range(len(soc_deficit_overflow_over_time)):
    #     soc_deficit_overflow_over_time[]
    #     ax.plot(steps, soc_deficit_overflow_over_time[ess])

    """ deficits """
    for ess in range(len(deficit_over_time)):
        ax.plot(steps, deficit_over_time[ess])
    for ess in range(len(overflow_over_time)):
        ax.plot(steps, overflow_over_time[ess])

    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='ESS deficits')


def show():
    plt.show()