# This file contains multiple key performance indicators (KPI) and other values of interest that can be derived from
# the microgrid object after a simulation. The output is a dictionary containing a dictionary for each households,
# electrolyzer and grid. Each KPI value is given as a list with two entries, the first being the value and the second
# being the unit.

import numpy as np
import collections


def get_kpi(microgrid):
    # Initiate the output dict.
    output_kpi = {}

    # Get a list of all agents.
    agent_list = [agent for agent in microgrid.agents]

    # Sum up tracking values for all households.
    pv_production_household_tot = 0.0
    demand_household_tot = 0.0

    # Print out the ratio of the energy needed and produced by the consumers.
    agents = microgrid.agents
    # Track the energy trade values for the agents.
    # Energy bought and sold [kWh].
    energy_bought_households_tot = 0.0
    energy_sold_households_tot = 0.0
    # Price payed and received for energy trades [EUR].
    money_earned_household_tot = 0.0
    money_spent_household_tot = 0.0
    # Count how many households there are and initialize household list.
    household_kpi = {}
    n_household = 0
    for this_agent_id in agents:
        if type(agents[this_agent_id]).__name__ == 'HouseholdAgent':
            this_agent = agents[this_agent_id]

            n_household += 1

            # Calculate the money earned and money spent [EUR].
            money_earned = 0.0
            money_spent = 0.0
            for ts_key in this_agent.wallet.payment_history:
                this_payment = this_agent.wallet.payment_history[ts_key]
                if this_payment > 0:
                    money_earned += this_payment
                elif this_payment < 0:
                    money_spent -= this_payment

            money_earned_household_tot += money_earned
            money_spent_household_tot += money_spent

            # Get the list with all energy trades made by this agent [list with unit kWh].
            energy_trade = np.array(this_agent.data.agent_measurements[this_agent_id]['traded_volume_over_time'])
            # Calculate the amount of electricity this agent bought and sold from the grid [kWh].
            energy_bought = float(sum(energy_trade[energy_trade > 0]))
            energy_sold = float(-sum(energy_trade[energy_trade < 0]))

            energy_bought_households_tot += energy_bought
            energy_sold_households_tot += energy_sold

            avg_sell_price = money_earned / energy_sold if money_earned > 0 else '-'
            avg_buy_price = money_spent / energy_bought if money_spent > 0 else '-'

            if this_agent.demand_tot == 0:
                # Case: there was no demand.
                los = "-"
            else:
                # Level of self sufficiency with 4 digits in total [%].
                los = "{:.4}".format(this_agent.pv_production_tot / this_agent.demand_tot * 100)

            pv_production_household_tot += this_agent.pv_production_tot
            demand_household_tot += this_agent.demand_tot

            # Save the KPI of interest.
            household_kpi[this_agent_id] = {}
            household_kpi[this_agent_id]['level_of_self_sufficiency'] = [los, '%']
            household_kpi[this_agent_id]['demand'] = [this_agent.demand_tot, 'kWh']
            household_kpi[this_agent_id]['energy_bought'] = [int(energy_bought), 'kWh']
            household_kpi[this_agent_id]['energy_sold'] = [int(energy_sold), 'kWh']
            household_kpi[this_agent_id]['money_earned'] = [int(money_earned), 'EUR']
            household_kpi[this_agent_id]['money_spent'] = [int(money_spent), 'EUR']
            household_kpi[this_agent_id]['avg_price_buy'] = [avg_buy_price, 'EUR/kWh']
            household_kpi[this_agent_id]['avg_price_sell'] = [avg_sell_price, 'EUR/kWh']

    household_key = 'Households'
    output_kpi[household_key] = household_kpi

    # Calculate the avg. electricity prices for all households [EUR/kWh].
    avg_sell_price_tot = \
        money_earned_household_tot / energy_sold_households_tot if energy_sold_households_tot > 0 else '-'
    avg_buy_price_tot = \
        money_spent_household_tot / energy_bought_households_tot if energy_bought_households_tot > 0 else '-'

    # Calculate the average expenses per household [EUR].
    avg_expense_household = (int(money_spent_household_tot - money_earned_household_tot) / n_household)

    output_kpi[household_key]['energy_bought_tot'] = [int(energy_bought_households_tot), 'kWh']
    output_kpi[household_key]['energy_sold_tot'] = [int(energy_sold_households_tot), 'kWh']
    output_kpi[household_key]['money_spent_tot'] = [int(money_spent_household_tot), 'EUR']
    output_kpi[household_key]['money_earned_tot'] = [int(money_earned_household_tot), 'EUR']
    output_kpi[household_key]['avg_buy_price_tot'] = [avg_buy_price_tot, 'EUR/kWh']
    output_kpi[household_key]['avg_sell_price_tot'] = [avg_sell_price_tot, 'EUR/kWh']
    output_kpi[household_key]['demand_tot'] = [int(demand_household_tot), 'kWh']
    output_kpi[household_key]['avg_expense_per_household'] = [avg_expense_household, 'EUR']

    if demand_household_tot == 0:
        los_tot = "-"
    else:
        los_tot = pv_production_household_tot / demand_household_tot * 100

    output_kpi[household_key]['level_of_self_sufficiency_tot'] = [los_tot, '%']

    # Calculate the wasted PV energy from the households [kWh].
    overflow = sum(sum(microgrid.data.overflow_over_time))
    if pv_production_household_tot == 0:
        share_overflow = '-'
    else:
        # Calculate the share of the produced PV power that is wasted [%].
        share_overflow = overflow / pv_production_household_tot * 100

    output_kpi[household_key]['energy_produced_tot'] = [int(pv_production_household_tot), 'kWh']
    output_kpi[household_key]['energy_wasted_tot'] = [overflow, 'kWh']
    output_kpi[household_key]['share_energy_wasted_tot'] = [share_overflow, '%']

    """ ELECTROLYZER """
    # Total energy bought by the electrolyzer [kWh].
    ely_key = 'Electrolyzer'
    output_kpi[ely_key] = {}
    energy_bought_ely = 0
    if ely_key in agents:
        ely = microgrid.agents[ely_key]
        # Money spent by the electrolyzer [EUR]
        cost_ely = 0
        for key in ely.wallet.payment_history:
            cost_ely -= ely.wallet.payment_history[key]

        # Amount of electricity bought by the electrolyzer [kWh].
        energy_bought_ely = sum(ely.track_bought_energy)
        # Average electricity cost [EUR/kWh].
        avg_elec_cost = cost_ely / energy_bought_ely
        # Calculate the estimated max. power of the electrolyzer (with an estimated efficiency of 65 %) [kW].
        ely_power_max = ely.area_cell * ely.cur_dens_max * ely.z_cell / (2 * ely.faraday) * ely.molarity * \
                        ely.upp_heat_val / 0.65

        output_kpi[ely_key]['energy_bought'] = [int(energy_bought_ely), 'kWh']
        output_kpi[ely_key]['cost'] = [int(cost_ely), 'EUR']
        output_kpi[ely_key]['avg_buy_price'] = [avg_elec_cost, 'EUR/kWh']
        output_kpi[ely_key]['max_power'] = [ely_power_max, 'kW']

    """ MARKET INFORMATION """
    market_key = 'Market'
    output_kpi[market_key] = {}
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

    output_kpi[market_key]['clearing_price_overview'] = \
        [track_clearing_price_ordered, 'Clearing price [EUR/kWh]: Number of occurrences [-]']

    # Calculate what ratio of the demand of the household was supplied by the grid.
    if microgrid.data.utility_presence is True:
        if microgrid.agents['Utility'].energy_sold_tot == 0:
            share_grid_supply = "-"
        else:
            share_grid_supply = \
                microgrid.agents['Utility'].energy_sold_tot / (demand_household_tot + energy_bought_ely) * 100

        output_kpi[market_key]['utility_energy_bought'] = [int(microgrid.agents['Utility'].energy_bought_tot), 'kWh']
        output_kpi[market_key]['utility_energy_sold'] = [int(microgrid.agents['Utility'].energy_sold_tot), 'kWh']
        output_kpi[market_key]['utility_share_supply_tot'] = [share_grid_supply, '%']

    return output_kpi
