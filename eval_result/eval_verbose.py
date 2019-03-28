'''
This function evaluates multiple values of interest and prints them out in a human readable fashion.
'''
import collections

def eval_print(microgrid, trade_deals_list_per_step):
    print("\n--------------------------------------------------------------------------------------------")
    print("                                 SIMULATION EVALUATION")
    print("--------------------------------------------------------------------------------------------\n")

    print("List of trades made is [id_seller, id_buyer, quantity, price*quantity]:")
    print(trade_deals_list_per_step)
    print()

    # Sum up tracking values for all households.
    pv_production_all = 0
    demand_all = 0

    # Print out the ratio of the energy needed and produced by the consumers.
    agents = microgrid.agents
    for this_agent_id in agents:
        if type(agents[this_agent_id]).__name__ == 'HouseholdAgent':
            this_agent = agents[this_agent_id]

            if this_agent.demand_tot == 0:
                # Case: there was no demand.
                los = "-"
            else:
                # Level of self sufficiency with 4 digits in total [%].
                los = "{:.4}".format(this_agent.pv_production_tot / this_agent.demand_tot * 100)
            print('Household with ID {} total demand is {:.4} kWh, it could be {} % self sufficient.'.format(
                this_agent_id, this_agent.demand_tot, los))

            pv_production_all += this_agent.pv_production_tot
            demand_all += this_agent.demand_tot

    if demand_all == 0:
        los_tot = "-"
    else:
        los_tot = pv_production_all / demand_all * 100
    print('\nAll households could be {:.4} % self sufficient.'.format(los_tot))

    overflow = sum(sum(microgrid.data.overflow_over_time))
    if pv_production_all == 0:
        share_overflow = '-'
    else:
        # Calculate the share of the produced PV power that is wasted [%].
        share_overflow = overflow / pv_production_all * 100

    print('\nAmount of PV energy produced is {:.4} kWh.'.format(pv_production_all))
    print('Amount of PV energy wasted is {:.4} kWh.'.format(overflow))
    print('Share of PV energy wasted is {:.4} %.'.format(share_overflow))

    # Print out information about the clearing price.
    clearing_price = [price[1] for price in microgrid.data.clearing_price_min_avg_max]
    # Loop through every time step and only consider times where the clearing quantity was greater 0.
    track_clearing_price = {}
    for i_step in range(len(clearing_price)):
        if microgrid.data.clearing_quantity[i_step] > 0:
            this_price = round(clearing_price[i_step], 4)
            if this_price in track_clearing_price:
                # Case: This clearing price was added to the dict before.
                track_clearing_price[this_price] += 1
            else:
                # Case: This price wasn't tracked before, thus a new dict entry must be made.
                track_clearing_price[this_price] = 1

    # Order the track_clearing_price dictionary by key (which is the price).
    track_clearing_price_ordered = collections.OrderedDict(sorted(track_clearing_price.items()))

    print('\nThe following clearing prices were created: ')
    for key in track_clearing_price_ordered:
        print('The price {} was achieved {} times.'.format(key, track_clearing_price_ordered[key]))


    # Calculate what ratio of the demand of the household was supplied by the grid.
    if microgrid.data.utility_presence is True:
        if microgrid.agents['Utility'].energy_sold_tot == 0:
            household_grid_usage = "-"
        else:
            household_grid_usage = demand_all / microgrid.agents['Utility'].energy_sold_tot

        print('\nFrom the total energy consumption {:.4} % was supplied by the grid.'.format(household_grid_usage))
        print('The utility grid bought {} kWh of electricity.'.format(microgrid.agents['Utility'].energy_bought_tot))
