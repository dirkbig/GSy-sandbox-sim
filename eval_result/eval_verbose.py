'''
This function evaluates multiple values of interest and prints them out in a human readable fashion.
'''
import collections
import numpy as np

def eval_print(microgrid, trade_deals_list_per_step):
    print("\n--------------------------------------------------------------------------------------------")
    print("                                 SIMULATION EVALUATION")
    print("--------------------------------------------------------------------------------------------\n")

    # print("List of trades made is [id_seller, id_buyer, quantity, price*quantity]:")
    # print(trade_deals_list_per_step)
    print()

    # Sum up tracking values for all households.
    pv_production_all = 0.0
    demand_all = 0.0

    # Print out the ratio of the energy needed and produced by the consumers.
    agents = microgrid.agents
    # Track the energy trade values for the agents.
    # Energy bought and sold [kWh].
    energy_bought_tot = 0.0
    energy_sold_tot = 0.0
    # Price payed and received for energy trades [EUR].
    money_earned_tot = 0.0
    money_spent_tot = 0.0

    for this_agent_id in agents:
        if type(agents[this_agent_id]).__name__ == 'HouseholdAgent':
            this_agent = agents[this_agent_id]

            # Calculate the money earned and money spent [EUR].
            money_earned = 0.0
            money_spent = 0.0
            for ts_key in this_agent.wallet.payment_history:
                this_payment = this_agent.wallet.payment_history[ts_key]
                if this_payment > 0:
                    money_earned += this_payment
                elif this_payment < 0:
                    money_spent -= this_payment

            money_earned_tot += money_earned
            money_spent_tot += money_spent

            # Get the list with all energy trades made by this agent [list with unit kWh].
            energy_trade = np.array(this_agent.data.agent_measurements[this_agent_id]['traded_volume_over_time'])
            # Calculate the amount of electricity this agent bought and sold from the grid [kWh].
            energy_bought = float(sum(energy_trade[energy_trade > 0]))
            energy_sold = float(-sum(energy_trade[energy_trade < 0]))

            energy_bought_tot += energy_bought
            energy_sold_tot += energy_sold

            avg_sell_price = money_earned/energy_sold if money_earned > 0 else '-'
            avg_buy_price = money_spent/energy_bought if money_spent > 0 else '-'

            if this_agent.demand_tot == 0:
                # Case: there was no demand.
                los = "-"
            else:
                # Level of self sufficiency with 4 digits in total [%].
                los = "{:.4}".format(this_agent.pv_production_tot / this_agent.demand_tot * 100)
            print('Household with ID {} total demand is {:.5} kWh, it could be {} % self sufficient.'.format(
                this_agent_id, this_agent.demand_tot, los) +
                  ' Avg. price selling {:.4} EUR/kWh; Avg. price buying {:.4} EUR/kWh;'.format(
                      avg_sell_price, avg_buy_price) +
                  ' Energy sold {:d} kWh; Energy bought: {:d} kWh; Income: {:d} EUR, Expense {:d} EUR.'.format(
                      int(energy_sold), int(energy_bought), int(money_earned), int(money_spent)))

            pv_production_all += this_agent.pv_production_tot
            demand_all += this_agent.demand_tot

    # Calculate the avg. electricity prices for all households [EUR/kWh].
    avg_sell_price_tot = money_earned_tot / energy_sold_tot if energy_sold_tot > 0 else '-'
    avg_buy_price_tot = money_spent_tot / energy_bought_tot if energy_bought_tot > 0 else '-'
    # Print avg. energy trade values for all house holds.
    print('\nIn total all houses sold {:d} kWh for {:d} EUR (avg. {:.4} EUR/kWh) and bought {:d} kWh for {:d} EUR' 
          ' (avg. {:.4} EUR/kWh)'.format(int(energy_sold_tot), int(money_earned_tot), avg_sell_price_tot,
                                         int(energy_bought_tot), int(money_spent_tot), avg_buy_price_tot))

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

    print('\nAmount of PV energy produced is {:d} kWh.'.format(int(pv_production_all)))
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
            share_grid_supply = "-"
        else:
            share_grid_supply = microgrid.agents['Utility'].energy_sold_tot / demand_all

        print('\nThe utility grid bought {} kWh of electricity.'.format(
            int(microgrid.agents['Utility'].energy_bought_tot)))
        print('The utility grid sold {} kWh of electricity.'.format(
            int(microgrid.agents['Utility'].energy_sold_tot)))
        print('From the total energy consumption {:.4} % was supplied by the grid.'.format(share_grid_supply * 100))

    # If an electrolyzer is present, print its characteristics.
    ely_key = 'Electrolyzer'
    if ely_key in microgrid.agents:
        ely = microgrid.agents[ely_key]
        # Money spent by the electrolyzer [EUR]
        cost = 0
        for key in ely.wallet.payment_history:
            cost -= ely.wallet.payment_history[key]

        # Amount of electricity bought by the electrolyzer [kWh].
        energy_bought = sum(ely.track_bought_energy)
        # Average electricity cost [EUR/kWh].
        avg_elec_cost = cost/energy_bought
        print('\n--------------- Electrolyzer -------------------')
        print('Electrolyzer bought {:.8} kWh for {:.7} EUR, avg. electricity price is {:.4} EUR/kWh'.format(
            energy_bought, cost, avg_elec_cost))

