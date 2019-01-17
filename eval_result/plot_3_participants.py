"""
This script plots the results for a run where 'Utility' and 'CommercialPv' are supplying power. The results are read
from a .csv file, in which the results are contained in the format

    seller, buyer, quantity [kWh], total cost [EUR]

Each row represents one time step, an example of a couple of time steps with supply by either Utility, PV or both looks
like:

Utility,Electrolyzer,51.69895911624681,0.0
Utility,Electrolyzer,51.69895854666277,0.15850900690406808
Utility,Electrolyzer,51.69895730103171,0.0
CommercialPv,Electrolyzer,0.166,0.0,Utility,Electrolyzer,51.53295911482054,0.0
CommercialPv,Electrolyzer,0.166,0.0,Utility,Electrolyzer,51.53295911248251,0.0
CommercialPv,Electrolyzer,5.24775,0.03205850475,Utility,Electrolyzer,46.45120909767002,0.28377043637766614
CommercialPv,Electrolyzer,5.24775,0.007866377249999999,Utility,Electrolyzer,46.45120911065989,0.06963036245687917
CommercialPv,Electrolyzer,15.129,0.07075833299999999,Utility,Electrolyzer,36.569958822494954,0.1710376974128089
CommercialPv,Electrolyzer,15.129,0.090728613,Utility,Electrolyzer,36.569957947728355,0.21931003781252695
CommercialPv,Electrolyzer,28.90075,0.5044625912499999,Utility,Electrolyzer,22.798206089806055,0.39794268729756466
CommercialPv,Electrolyzer,28.90075,0.32917954250000003,Utility,Electrolyzer,22.79820909060383,0.25967160154197766
CommercialPv,Electrolyzer,45.214749999999995,0.0910625065,Utility,Electrolyzer,6.484207194566217,0.013059193289856361
CommercialPv,Electrolyzer,45.214749999999995,0.0,Utility,Electrolyzer,6.484208884336823,0.0
CommercialPv,Electrolyzer,51.69895901841166,0.948055510479633
CommercialPv,Electrolyzer,51.69895907801826,0.4355637302323039

"""

import matplotlib.pyplot as plt
import numpy as np
import csv


''' SET UP PLOT OUTPUT, THAT CAN BE RENDERED DIRECTLY BY LATEX'''
# Using the pgf backend, matplotlib can export figures as pgf drawing commands that can be processed with LaTeX.
# matplotlib.use('pgf')


''' LOAD THE RESULTS '''
# Load the result file and save the total trade quantity [kWh] and the total cost for the quantity [EUR].
trade_quantity = {'Utility': [], 'CommercialPv': []}
cost = {'Utility': [], 'CommercialPv': []}
with open("../test_result.csv", 'r', newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    counter = 0
    for row in csv_reader:
        # First add a zero to all the lists of interest.
        trade_quantity['Utility'].append(0.0)
        trade_quantity['CommercialPv'].append(0.0)
        cost['Utility'].append(0.0)
        cost['CommercialPv'].append(0.0)
        # Now check the actual value for this time step and, if there is one, overwrite the zero that was just set.
        for item in row:
            if counter % 4 == 0:
                this_from = item
            elif counter % 4 == 1:
                this_to = item
            elif counter % 4 == 2:
                this_quantity = float(item)
            elif counter % 4 == 3:
                # Total cost [EUR]
                this_cost = float(item)

            if counter % 4 == 3:
                # Case: 4 values in one row, which make up one bid, have been taken into account. Therfore save the bid.
                trade_quantity[this_from][-1] = this_quantity
                cost[this_from][-1] = this_cost

            counter += 1




# Calculate the electricity price for that time step [EUR/kWh].
elec_price = []
for i in range(len(trade_quantity['Utility'])):
    if trade_quantity['CommercialPv'][i] == 0:
        # Case: There was no trade with the PV system.
        if trade_quantity['Utility'][i] == 0:
            # Case: There also was no trade with the utility grid, therefore set the trading price to zero.
            elec_price.append(0)
        else:
            # There was trading with the utility grid, therefore use the utility transaction to determine the clearing
            # price [EUR/kWh].
            elec_price.append(cost['Utility'][i] / trade_quantity['Utility'][i])
    else:
        # Case: Clearing price can be derived from the commercial PV [EUR/kWh].
        elec_price.append(cost['CommercialPv'][i] / trade_quantity['CommercialPv'][i])

# Calculate the total costs [EUR].
cost_tot = []
for i in range(len(elec_price)):
    cost_tot.append(cost['Utility'][i] + cost['CommercialPv'][i])


print('Data loaded successfully')

''' PLOT THE RESULTS '''
""" Plot """
# font = {'weight': 'bold', 'size': 18}
fig, (ax1, ax3) = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3.5, 1]}, figsize=(5, 4))
# If the axis labels are cut of, the following settings can be used to adjust the plot accordingly.
plt.gcf().subplots_adjust(left=0.15)
plt.gcf().subplots_adjust(right=0.85)
plt.gcf().subplots_adjust(bottom=0.2)
plt.gcf().subplots_adjust(top=0.98)
# Plot 1.1
# ax1.tick_params(axis='both', which='major')
# ax1.tick_params(axis='both', which='major', labelsize=font['size'])
ax1.step(list(range(len(cost_tot))), cost_tot, 'k')
ax1.set_ylabel("Total costs [EUR]")
# ax1.set_ylabel("Total costs [EUR]", fontsize=font['size'], fontweight=font['weight'])
# Plot 1.2
ax2 = ax1.twinx()
ax2.step(list(range(len(trade_quantity['Utility']))), trade_quantity['Utility'], color='r')
ax2.step(list(range(len(trade_quantity['CommercialPv']))), trade_quantity['CommercialPv'], color='g')
ax2.set_ylabel("Trade quantity [kWh]", color='r')
# ax2.set_ylabel("Trade quantity [kWh]", color='r', fontsize=font['size'], fontweight=font['weight'])
# ax2.tick_params(axis='both', which='major')
# ax2.tick_params(axis='both', which='major', labelsize=font['size'])
# Plot 2
ax3.step(list(range(len(elec_price))), np.array(elec_price), color='g')
ax3.set_ylabel("Electricty price [EUR/kWh]", color='g')
# ax3.set_ylabel("Electricty price [EUR/kWh]", color='g', fontsize=font['size'], fontweight=font['weight'])
# ax3.tick_params(axis='both', which='major', labelsize=font['size'])
ax3.set_xlabel("Step [-]")
# ax3.set_xlabel("Step [-]", fontsize=font['size'], fontweight=font['weight'])
# Show the plot.
# plt.show()
plt.savefig('example.pdf')
plt.savefig('example.pgf')
print('Plot done')

