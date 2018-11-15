from source import microgrid_environment

import logging
logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')

fh = logging.FileHandler('pac_log.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
grid_log.addHandler(fh)

trade_deals_list_per_step = {}


def extract_data():
    trade_deals_list_per_step[microgrid.step_count] = microgrid.auction.trade_pairs


def create_microgrid():
    """create microgrid"""
    microgrid_ = microgrid_environment.MicroGrid()
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info('Step %d' % microgrid.step_count)
    extract_data()

microgrid = create_microgrid()

for step in range(microgrid.data.num_steps):
    print("step", microgrid.step_count)
    step_microgrid()

assert microgrid.step_count == microgrid.data.num_steps
microgrid.data.plots()


print(trade_deals_list_per_step)

