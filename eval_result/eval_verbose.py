'''
This function evaluates multiple values of interest and prints them out in a human readable fashion.
'''


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

    # Calculate what ratio of the demand of the household was supplied by the grid.
    if microgrid.data.utility_presence is True:
        if microgrid.agents['Utility'].energy_sold_tot == 0:
            household_grid_usage = "-"
        else:
            household_grid_usage = demand_all / microgrid.agents['Utility'].energy_sold_tot

        print('\nFrom the total energy consumption {:.4} % was supplied by the grid.'.format(household_grid_usage))
        print('The utility grid bought {} kWh of electricity.'.format(microgrid.agents['Utility'].energy_bought_tot))
