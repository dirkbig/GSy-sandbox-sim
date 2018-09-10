from source.const import *
from source import microgrid_env
import logging
logging.basicConfig(level=logging.INFO)
grid_log = logging.getLogger('run_microgrid')


def run_microgrid_sim(_auction_type):
    """create microgrid"""
    microgrid_ = microgrid_env.MicroGrid(_auction_type)
    grid_log.info('microgrid class created')
    return microgrid_


def step_microgrid():
    microgrid.sim_step()
    grid_log.info("Step %d", microgrid.step)


microgrid = run_microgrid_sim(auction_type)

# TODO: model this for a 24h simulation in a for-loop

for step in range(num_steps):
    step_microgrid()

