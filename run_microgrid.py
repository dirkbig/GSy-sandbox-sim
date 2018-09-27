from source import microgrid_environment
from source.const import *

import logging
logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')


def create_microgrid():
    """create microgrid"""
    microgrid_ = microgrid_environment.MicroGrid()
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info('Step %d' % microgrid.step_count)


microgrid = create_microgrid()

# TODO: model this for a 24h simulation in a for-loop using 24h profiles

for step in range(microgrid.data.num_steps):
    step_microgrid()
    print("step", microgrid.step_count)

