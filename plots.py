import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import numpy as np
sns.set()
#mpl.use('pdf')

#plt.rcParams["font.family"] = 'Century Schoolbook'

mpl.rc('font', family='serif', serif='Roboto Light')
#plt.rc('text', usetex=False)
plt.rc('xtick', labelsize=8)
plt.rc('ytick', labelsize=8)
plt.rc('axes', labelsize=8)

# width of images in the PDF [inch].
width = 5.38
default_height = width / 1.618
# Font for plots
font = "Century Schoolbook"


def clearing_snapshot(clearing_quantity, clearing_price, sorted_x_y_y_pairs_list):
    x_quantities = [0]
    y_bid_prices = [0]
    y_offer_prices = [0]

    for segment in sorted_x_y_y_pairs_list:
        x_quantities.append(segment[0])
        y_bid_prices.append(segment[1])
        y_offer_prices.append(segment[2])

    fig, ax = plt.subplots()

    ax.step(x_quantities, y_bid_prices, label='bids')
    ax.step(x_quantities, y_offer_prices, label='offers')
    if clearing_quantity is not None:
        ax.axvline(x=clearing_quantity, color='black', linestyle='--')
        if clearing_price is not None:
            ax.axhline(y=clearing_price, color='black', linestyle='--')

    ax.legend(loc='center right')
    ax.set(xlabel='quantity', ylabel='price',
           title='clearing markets aggregate demand and supply blocks')
    plt.show()


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

    ax.legend(loc='center right', bbox_to_anchor=(1, 1), ncol=3, fontsize=8)


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
    f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    """ overflows / curtailment """
    # for ess in range(len(soc_deficit_overflow_over_time)):
    #     soc_deficit_overflow_over_time[]
    #     ax.plot(steps, soc_deficit_overflow_over_time[ess])

    """ deficits """
    for ess in range(len(deficit_over_time)):
        ax1.step(steps, deficit_over_time[ess])
    for ess in range(len(overflow_over_time)):
        ax2.step(steps, overflow_over_time[ess])

    ax1.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='ESS deficits, unmatched loads')
    ax2.set(xlabel='sim steps', ylabel='kWh / step-interval',
           title='ESS overflow, forced curtailment of generation')


def clearing_over_utility_price(num_steps, utility_price, clearing_price_min_avg_max, clearing_quantity):
    clearing_price_avg = [price[1] for price in clearing_price_min_avg_max]

    steps = range(num_steps)
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.84, top=.97)

    # ax.step(steps, utility_price[:num_steps], label='Utility price')
    # ax.step(steps, clearing_price_avg, label='Clearing price')

    line1 = ax.step(steps, clearing_quantity, label='Trading quantity', color='b')

    # line2 = ax.plot(steps, utility_price[:num_steps], label='Price: Utility', linestyle='--', drawstyle='steps')
    ax.set_xlabel('sim steps', fontname=font)
    ax.set_ylabel("Trading quantity [kWh]", fontname=font)
    # ax.set(xlabel='sim steps', ylabel='Electricity costs [EUR/kWh]', title='Comparison Utility rate - Clearing rate')

    ax2 = ax.twinx()
    ax2.grid(False)
    line3 = ax2.plot(steps, clearing_price_avg,
                     label='Clearing price', drawstyle='steps', color='r', marker=',', linestyle=' ')
    ax2.set_ylabel('Clearing price [EUR/kWh]', color='r', fontname=font)

    all_line = line1 + line3
    label_name = [this_line.get_label() for this_line in all_line]
    h_legend = ax2.legend(all_line, label_name, loc='center right', shadow=True)
    plt.setp(h_legend.texts, family=font)
    fig.set_size_inches(width, default_height)
    fig.savefig('clearing_over_util.pdf')


def clearing_quantity_over_demand(num_steps, clearing_quantity, demand):
    steps = range(num_steps)
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.97, top=.97)

    ax.step(steps, clearing_quantity, label='Clearing quantity')
    ax.step(steps, demand, label='Household Demand')

    h_legend = ax.legend(loc='center right', shadow=True)
    plt.setp(h_legend.texts, family=font)
    # ax.set(xlabel='sim steps', ylabel='Electricity quantity [kWh]', title='Trading quantity over household demand')
    ax.set_xlabel('sim steps', fontname=font)
    ax.set_ylabel('Trading quantity [kWh]', fontname=font)
    fig.set_size_inches(width, default_height)
    fig.savefig('clearing_over_demand.pdf')


def clearing_quantity(num_steps, clearing_quantity):

    steps = range(num_steps)
    fig, ax = plt.subplots()

    ax.step(steps, clearing_quantity)

    ax.set(xlabel='sim steps', ylabel='Clearing quantity [kWh]', title='Clearing quantity')


def traded_volume_over_time(num_steps, agent_measurements):

    f, ax1 = plt.subplots()

    for agent in agent_measurements:
        ax1.bar(np.arange(num_steps), agent_measurements[agent]["traded_volume_over_time"])
        label = agent
    # ax.title('Traded volume per agent')

    # ax.legend((p1[0], p2[0]), ('Men', 'Women'))

def electrolyzer(num_steps, electrolyzer):
    steps = range(num_steps)
    fig, (ax1, ax2) = plt.subplots(2, 1)
    ax1.step(steps, electrolyzer.track_stored_hydrogen)
    ax1.set(xlabel='sim steps', ylabel='Stored hydrogen [kg]', title='Electrolyzer')

    ax2.step(steps, electrolyzer.track_bought_energy)
    ax2.set(xlabel='sim steps', ylabel='Bought electricity [kWh]')


def trade_prices_min_avg_max():
    pass


def show():
    plt.show()
