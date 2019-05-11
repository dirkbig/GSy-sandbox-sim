from source import microgrid_environment
from eval_result.eval_verbose import eval_print
from grid_config_profile import ConfigurationUtility50prosumerEly as Config
# from grid_config import ConfigurationMixin as Config

import logging

logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')

fh = logging.FileHandler('pac_log.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
grid_log.addHandler(fh)

trade_deals_list_per_step = {}
clearing_price = {}
clearing_quantity = {}


def extract_data():
    trade_deals_list_per_step[microgrid.step_count] = microgrid.auction.trade_pairs
    clearing_price[microgrid.step_count] = microgrid.auction.clearing_price
    clearing_quantity[microgrid.step_count] = microgrid.auction.clearing_quantity


def create_microgrid():
    """create microgrid"""
    microgrid_ = microgrid_environment.MicroGrid(Config())
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info('Step %d' % microgrid.step_count)
    extract_data()

# Create multiple options for the bidding price of the ely, which consists of 4 prices. The prices have a range from 6
# to 24 ct/kWh and the distance of the prices varies between 2, 4 or 6 ct/kWh.


# Distance of 6 ct/kWh.
ely_bidding_price = [[6, 12, 18, 24]]
# Distance of 4 ct/kWh.
ely_bidding_price += [[i, i+4, i+8, i+12] for i in range(6, 14, 2)]
# Distance of 2 ct/kWh.
ely_bidding_price += [[i, i+2, i+4, i+6] for i in range(6, 20, 2)]

for i_run in range(len(ely_bidding_price)):
    microgrid = create_microgrid()
    # Update ely bidding prices [EUR/kWh].
    microgrid.agents["Electrolyzer"].stepwise_bid_price = [i / 100 for i in ely_bidding_price[i_run]]
    for step in range(microgrid.data.num_steps):
        if step % 1000 == 0:
            print("\n*******************************************************")
            print("                     step", microgrid.step_count)
            print("*******************************************************")
        step_microgrid()

    assert microgrid.step_count == microgrid.data.num_steps

    write_output_to_csv = False
    if write_output_to_csv:
        import csv

        with open("test_result.csv", "w", newline='') as file:
            writer = csv.writer(file)
            for i in range(len(trade_deals_list_per_step)):
                this_row = []
                if trade_deals_list_per_step[i + 1] is None:
                    # Case: This trade entry is None. While a time step without a trade might lead to an entry of None or
                    # an empty list, make all Nones to empty lists for further processing.
                    trade_deals_list_per_step[i + 1] = []
                if len(trade_deals_list_per_step[i + 1]) > 0:
                    for row_entry in trade_deals_list_per_step[i + 1]:
                        this_row += row_entry
                else:
                    this_row = ['No trade was made']

                writer.writerow(this_row)

    # Save the session result to, for example, create other plots later on.
    save_session = False

    if save_session:
        import pickle

        result_loc = 'eval_result/stored_session/'
        result_str = 'result_{}_{}_{}_{}.pkl'.format(*ely_bidding_price[i_run])
        filehandler = open(result_loc+result_str, 'wb')
        pickle.dump(microgrid, filehandler)
        filehandler.close()
        # dill.dump_session(session_name)
        print('Session saved at', result_loc)

# eval_print(microgrid)
# microgrid.data.plots()

print("\n*******************************************************")
print("                  Simulation finished")
print("*******************************************************")


