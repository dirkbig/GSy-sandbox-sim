'''
This function evaluates multiple values of interest and prints them out in a human readable fashion.
'''
import collections
from .get_kpi import get_kpi


def eval_print(microgrid):
    print("\n--------------------------------------------------------------------------------------------")
    print("                                 SIMULATION EVALUATION")
    print("--------------------------------------------------------------------------------------------")

    """ HOUSEHOLDS """
    print("\n--------------- HOUSEHOLDS -------------------\n")

    # Load the KPI.
    kpi = get_kpi(microgrid)
    # Print out the ratio of the energy needed and produced by the consumers.
    agents = microgrid.agents
    household_key = 'Households'

    for this_agent_id in agents:
        if type(agents[this_agent_id]).__name__ == 'HouseholdAgent':
            this_kpi = kpi[household_key][this_agent_id]

            print('Household with ID {} total demand is {:.5} kWh, it could be {} % self sufficient.'.format(
                this_agent_id, this_kpi['demand'][0], this_kpi['level_of_self_sufficiency'][0]) +
                  ' Avg. price selling {:.4} EUR/kWh; Avg. price buying {:.4} EUR/kWh;'.format(
                      this_kpi['avg_price_sell'][0], this_kpi['avg_price_buy'][0]) +
                  ' Energy sold {:d} kWh; Energy bought: {:d} kWh; Income: {:d} EUR, Expense {:d} EUR.'.format(
                      this_kpi['energy_sold'][0], this_kpi['energy_bought'][0], this_kpi['money_earned'][0],
                      this_kpi['money_spent'][0]))

    kpi_h = kpi[household_key]

    print('\nIn total all houses sold {:d} kWh for {:d} EUR (avg. {:.4} EUR/kWh) and bought {:d} kWh for {:d} EUR' 
          ' (avg. {:.4} EUR/kWh)'.format(kpi_h['energy_sold_tot'][0], kpi_h['money_earned_tot'][0],
                                         kpi_h['avg_sell_price_tot'][0], kpi_h['energy_bought_tot'][0],
                                         kpi_h['money_spent_tot'][0], kpi_h['avg_buy_price_tot'][0]))
    print('All households had a demand of {} kWh. On average each household payed {} EUR over the simulation time.'
          .format(kpi_h['demand_tot'][0], kpi_h['avg_expense_per_household'][0]))
    print('\nAll households could be {:.4} % self sufficient.'.format(kpi_h['level_of_self_sufficiency_tot'][0]))
    print('\nAmount of PV energy produced is {:d} kWh.'.format(kpi_h['energy_produced_tot'][0]))
    print('Amount of PV energy wasted is {:.4} kWh.'.format(kpi_h['energy_wasted_tot'][0]))
    print('Share of PV energy wasted is {:.4} %.'.format(kpi_h['share_energy_wasted_tot'][0]))

    """ ELECTROLYZER """
    # Total energy bought by the electrolyzer [kWh].
    ely_key = 'Electrolyzer'
    if ely_key in agents:
        kpi_ely = kpi[ely_key]
        print('\n--------------- ELECTROLYZER -------------------\n')
        print('Electrolyzer bought {} kWh for {} EUR, avg. electricity price is {:.4} EUR/kWh'.format(
            kpi_ely['energy_bought'][0], kpi_ely['cost'][0], kpi_ely['avg_buy_price'][0]))
        print("Electrolyzer max. power is estimated {:.5} kW".format(kpi_ely['max_power'][0]))

    """ MARKET INFO """
    market_key = 'Market'
    kpi_market = kpi[market_key]
    print("\n--------------- CLEARING PRICE -------------------")
    track_clearing_price_ordered = kpi_market['clearing_price_overview'][0]
    print('\nThe following clearing prices were created: ')
    for key in track_clearing_price_ordered:
        print('The price {} was achieved {} times.'.format(key, track_clearing_price_ordered[key]))

    """ UTILITY GRID """
    print("\n--------------- UTILITY GRID -------------------")
    if microgrid.data.utility_presence is True:
        print('\nThe utility grid bought {} kWh of electricity.'.format(kpi_market['utility_energy_bought'][0]))
        print('The utility grid sold {} kWh of electricity.'.format(kpi_market['utility_energy_sold'][0]))
        print('From the total energy consumption {:.4} % was supplied by the grid.'.format(
            kpi_market['utility_share_supply_tot'][0]))

