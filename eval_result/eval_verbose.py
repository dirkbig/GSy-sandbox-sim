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

    agents = microgrid.agents

    # Sum up tracking values for all households.
    pv_production_all = 0
    demand_all = 0
    # Print out the ratio of the energy needed and produced by the consumers.
    for this_agent_id in agents:
        if type(agents[this_agent_id]).__name__ == 'HouseholdAgent':
            this_agent = agents[this_agent_id]
            # Level of self sufficiency.
            los = this_agent.pv_production_tot / this_agent.demand_tot
            print('Household with ID {} total demand is {:.4} kWh, it could {:.4} % self sufficient.'.format(
                this_agent_id, this_agent.demand_tot, los * 100))

            pv_production_all += this_agent.pv_production_tot
            demand_all += this_agent.demand_tot

    print('\nAll households could be {:.4} % self sufficient.'.format(pv_production_all/demand_all*100))

    # Calculate what ratio of the demand of the household was supplied by the grid.
    household_grid_usage = demand_all / microgrid.agents['Utility'].energy_sold_tot

    print('\nFrom the total energy consumption {:.4} % was supplied by the grid.'.format(household_grid_usage))
    print('The utility grid bought {} kWh of electricity.'.format(microgrid.agents['Utility'].energy_bought_tot))
