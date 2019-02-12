import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
sns.set()


def clearing_snapshot(clearing_quantity, clearing_price, sorted_x_y_y_pairs_list):
    # TODO: export these demand/supply curves
    x_quantities = [0]
    y_bid_prices = [0]
    y_offer_prices = [0]

    for i in range(len(sorted_x_y_y_pairs_list)):
        x_quantities.append(sorted_x_y_y_pairs_list[i][0])
        y_bid_prices.append(sorted_x_y_y_pairs_list[i][1])
        y_offer_prices.append(sorted_x_y_y_pairs_list[i][2])

    fig, ax = plt.subplots()

    ax.step(x_quantities, y_bid_prices, label='bids')
    ax.step(x_quantities, y_offer_prices, label='offers')
    if clearing_quantity is not None:
        ax.axvline(x=clearing_quantity, color='black', linestyle='--')
        if clearing_price is not None:
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

    ax.step(steps, avg_load)
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

    ax.step(steps, avg_pv_output)
    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='avg PV output')


def plot_fuel_station_profile(num_steps, fuel_station_profile):

    steps = range(num_steps)
    fig, ax = plt.subplots()
    ax.step(steps, fuel_station_profile)
    ax.set(xlabel='sim steps', ylabel='H2 [kg] / step-interval',
           title='Load fuel station ')


def total_generation_vs_consumption(num_steps, pv_array, load_array):

    steps = range(num_steps)
    total_load = np.ndarray.sum(np.array(load_array), axis=0) / len(load_array)
    total_pv_output = np.sum(pv_array, axis=0)/ len(pv_array)

    fig, ax = plt.subplots()
    ax.step(steps, total_load, label='total load')
    ax.step(steps, total_pv_output, label='total pv')

    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='Total generation vs. consumption')

    ax.legend(loc='lower right', bbox_to_anchor=(1, 1), ncol=3, fontsize=8)


def soc_over_time(num_steps, soc_per_agent_over_time_array):

    """ throw away all rows filled with zero """
    # TODO: delete rows that are all zero, only non-zero rows are relevant

    steps = range(num_steps)
    fig, ax = plt.subplots()
    for ess in range(len(soc_per_agent_over_time_array)):
        ax.step(steps, soc_per_agent_over_time_array[ess])
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
        ax.step(steps, deficit_over_time[ess])
    for ess in range(len(overflow_over_time)):
        ax.step(steps, overflow_over_time[ess])

    ax.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='ESS deficits')


def clearing_over_utility_price(num_steps, utility_price, clearing_price, clearing_quantity):

    steps = range(num_steps)
    fig, ax = plt.subplots()


    ax.step(steps, utility_price[:num_steps], label='Utility price')
    ax.step(steps, clearing_price, label='Clearing price')

    ax.legend(loc='upper center', shadow=True, fontsize='x-large')

    line1 = ax.plot(steps, clearing_price, label='Price: Clearing', drawstyle='steps')
    line2 = ax.plot(steps, utility_price[:num_steps], label='Price: Utility', linestyle='--', drawstyle='steps')
    ax.set(xlabel='sim steps', ylabel='Eletricity costs [EUR/kWh]', title='Comparison utility - clearing price')


    ax2 = ax.twinx()
    ax2.step(steps, clearing_quantity, color='r')

    ax2.grid(False)
    line3 = ax2.step(steps, clearing_quantity, label='Trading quantity', color='r')
    ax2.set_ylabel("Trade quantity [kWh]", color='r')

    all_line = line1 + line2 + line3
    label_name = [this_line.get_label() for this_line in all_line]
    ax.legend(all_line, label_name, loc='center right', shadow=True)


def clearing_quantity_over_demand(num_steps, clearing_quantity, demand):
    steps = range(num_steps)
    fig, ax = plt.subplots()

    ax.step(steps, clearing_quantity, label='Clearing quantity')
    ax.step(steps, demand, label='Household Demand')

    ax.legend(loc='upper center', shadow=True, fontsize='x-large')
    ax.set(xlabel='sim steps', ylabel='Electricity quantity [kWh]', title='Trading quantity over household demand')



def clearing_quantity(num_steps, clearing_quantity):

    steps = range(num_steps)
    fig, ax = plt.subplots()

    ax.step(steps, clearing_quantity)

    ax.set(xlabel='sim steps', ylabel='Clearing quantity [kWh]', title='Clearing quantity')


def show():
    plt.show()