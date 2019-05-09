# This script allows to load a saved result and plot the results again as well as print the results output.

import dill
from eval_result.eval_verbose import eval_print

# Define the path to the saved session
location_saved_session = 'eval_result/stored_session/ResultUtility50prosumerEly.pkl'
# Load the saved session
dill.load_session(location_saved_session)
print('Loaded session')

eval_print(microgrid, trade_deals_list_per_step)
microgrid.data.plots()