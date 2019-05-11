# This script allows to load a saved result and plot the results again as well as print the results output.

import pickle
from eval_result.eval_verbose import eval_print
from eval_result.get_kpi import get_kpi

"""
# Define the path to the saved session
location_saved_result = 'eval_result/stored_session/test_pkl.pkl'
filehandler = open(location_saved_result, 'rb')
# Load the saved session
microgrid = pickle.load(filehandler)
filehandler.close()
#dill.load_session(location_saved_session)
print('Loaded session')

eval_print(microgrid)
microgrid.data.plots()
"""

""" EVALUATE MULTIPLE RESULTS """
# Define the names of the results.
ely_bidding_price = [[6, 12, 18, 24]]
ely_bidding_price += [[i, i+4, i+8, i+12] for i in range(6, 14, 2)]
ely_bidding_price += [[i, i+2, i+4, i+6] for i in range(6, 20, 2)]
# Initiate values of interest.
household_earnings = {}

for i_result in range(len(ely_bidding_price)):
    print('Load results {}'.format(i_result))
    # Get the name of this result.
    result_loc = 'eval_result/stored_session/'
    result_str = 'result_{}_{}_{}_{}.pkl'.format(*ely_bidding_price[i_result])
    this_result_name = result_loc + result_str
    # Load the result.
    filehandler = open(this_result_name, 'rb')
    microgrid = pickle.load(filehandler)
    filehandler.close()

    # Get values of interest.
    this_kpi = get_kpi(microgrid)

    household_earnings[i_result] = this_kpi['Households']['avg_expense_per_household']

print('\nResults are: \n')

print(household_earnings)
















