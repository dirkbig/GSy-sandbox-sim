""" DATA """
import logging
data_methods_log = logging.getLogger('run_microgrid.constants')

""" Constants """
ambient_temp = 293.15
num_minutes_in_a_day = 1440

""" Money matters """
initial_coins_household = 10000000000

""" Simulation environment """
num_steps = int(96*15)
market_interval = 15  # minutes
# Start time in UNIX (e.g. 1420070400 for 00:00:00-01.01.2015).
# start_time = 1420070400

""" ESS constants"""
# initial_capacity = 0
# max_size_ess = 10
horizon = 24
constraints_setting = "off"  # "off" or "on"
if constraints_setting == 'off':
    data_methods_log.warning("Physical battery constraints are not active")


# data_methods_log.info("num_households %s" % num_households)
data_methods_log.info("market_interval %s [min]" % market_interval)


