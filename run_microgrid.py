from source import MicrogridEnvironment
from source.const import *

import logging
logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')

fh = logging.FileHandler('pac_log.txt')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
grid_log.addHandler(fh)


def run_microgrid_sim(_auction_type):
    """create microgrid"""
    microgrid_ = MicrogridEnvironment.MicroGrid()
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info("Step %d", microgrid.step)


microgrid = run_microgrid_sim(auction_type)

# TODO: model this for a 24h simulation in a for-loop

for step in range(num_steps):
    step_microgrid()

