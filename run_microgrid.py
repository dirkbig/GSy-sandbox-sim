from source import microgrid_environment

import logging
logging.basicConfig(level=logging.ERROR)
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

for step in range(microgrid.data.num_steps):
    print("step", microgrid.step_count)
    step_microgrid()

assert microgrid.step_count == microgrid.data.num_steps
microgrid.data.plots()

