from mesa import Agent
import logging
utility_log = logging.getLogger('run_microgrid.utility grid')


class UtilityAgent(Agent):
    """ Utility agent is created by calling this function """
    def __init__(self, model):
        self.model = model
        pass


