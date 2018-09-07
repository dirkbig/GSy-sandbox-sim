import const
import logging
device_log = logging.getLogger('device')


class ESS(object):
    def __init__(self, agent):
        device_log.info('ESS added to house %d', agent.id)
        super().__init__()
        """parameters"""
        self.max_capacity = agent.data.capacity[agent.id]
        """ESS state variables"""
        self.soc_actual = const.initial_capacity * self.max_capacity
        """data collection from Household"""
        self.load_profile = agent.data.load_profile[agent.id]
        self.production_profile = agent.data.production_profile[agent.id]
        """initial values"""
        self.soc_preferred = None
        self.surplus = None

    def soc_preferred_calc(self):
        """forecast of load minus (personal) productions over horizon expresses preferred soc of ESS"""
        # self.soc_preferred = sum(self.load_horizon) - sum(self.production_horizon)
        return

    def ess_demand_calc(self, agent):
        """calculates the demand expresses by a household's ESS"""
        self.soc_preferred_calc()
        if self.soc_preferred is None:
            self.soc_preferred = 0
        self.surplus = agent.production - agent.load - (self.soc_preferred - self.soc_actual)

    def update_ess_state(self):
        self.soc_actual = self.soc_actual + self.balance
        assert self.soc_actual <= self.max_capacity and self.soc_actual > 0


class PVPanel(object):
    def __init__(self):
        """PVPanel device"""


class Electrolyzer(object):
    def __init__(self):
        """ Electrolyzer device"""


class GeneralLoad(object):
    def __init__(self):
        """ General load device """



