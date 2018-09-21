from source import microgrid_environment
from source.const import *

import logging
logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')


def run_microgrid_sim(_auction_type):
    """create microgrid"""
    microgrid_ = microgrid_environment.MicroGrid()
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info('Step %d' % microgrid.step_count)


microgrid = run_microgrid_sim(auction_type)

# TODO: model this for a 24h simulation in a for-loop using 24h profiles

for step in range(num_steps):
    step_microgrid()

