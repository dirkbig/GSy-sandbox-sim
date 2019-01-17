import matplotlib.pyplot as plt
import numpy as np
import csv


''' SET UP PLOT OUTPUT, THAT CAN BE RENDERED DIRECTLY BY LATEX'''
# Using the pgf backend, matplotlib can export figures as pgf drawing commands that can be processed with LaTeX.
# matplotlib.use('pgf')


''' LOAD THE RESULTS '''
# Load the result file and save the total trade quantity [kWh] and the total cost for the quantity [EUR].
trade_quantity = []
cost_tot = []
with open("../test_result.csv", 'r', newline='') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        trade_quantity.append(float(row[2]))
        cost_tot.append(float(row[3]))

# Calculate the electricity price for that time step [EUR/kWh].
elec_price = []
for i in range(len(trade_quantity)):
    elec_price.append(cost_tot[i] / trade_quantity[i])

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
ax2.step(list(range(len(trade_quantity))), trade_quantity, color='r')
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

