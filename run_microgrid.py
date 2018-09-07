import microgrid_env
import logging
logging.basicConfig(level=logging.WARNING)
grid_log = logging.getLogger('run_microgrid')

auction_type = 'pay_as_clear'
num_step = 10


def run_microgrid_sim(_auction_type):
    """create microgrid"""
    microgrid = microgrid_env.MicroGrid(_auction_type)
    grid_log.info('microgrid class created')
    microgrid.sim_step()


run_microgrid_sim(auction_type)

