from source.const import *
from source.device_methods import *
import logging
device_log = logging.getLogger('run_microgrid.device')


class ESS(object):
    def __init__(self, agent, ess_data):
        device_log.info('ESS added to house %d', agent.id)
        super().__init__()
        self.agent = agent

        """ ESS characteristics extracted from ess_data """
        self.initial_capacity = ess_data[0]
        self.max_capacity = ess_data[1]
        self.soc_actual = self.initial_capacity * self.max_capacity
        print('soc_actual house %d =' % self.agent.id , self.soc_actual)

        """ initialization of all information the smart-ESS needs for its strategy  """
        self.next_interval_load = None
        self.next_interval_production = None
        self.next_interval_electrolyzer_load = None

        """ strategy variables """
        self.total_supply_from_devices_at_step = None
        self.soc_preferred = None
        self.surplus = None

    def update_from_household_devices(self):
        """ ask an update from all devices within the information sphere
            (this is of course, all devices within the same house """

        current_step = self.agent.model.step_count
        print('devices list of household %d:' % self.agent.id, self.agent.devices)

        total_supply_from_devices = 0
        for device in self.agent.devices:
            if device != 'ESS':
                total_supply_from_devices += self.agent.devices[device].uniform_call_to_device(current_step)
                print(self.agent.devices[device].uniform_call_to_device(current_step))
        self.total_supply_from_devices_at_step = total_supply_from_devices

    def uniform_call_to_device(self, current_step):
        print("ESS of house %s checking in" % self.agent.id)
        return

    def ess_demand_calc(self, current_step):
        """calculates the demand expresses by a household's ESS"""
        self.update_from_household_devices()

        self.soc_preferred_calc()
        if self.soc_preferred is None:
            self.soc_preferred = 0

        """ The logic here is straight forwards; what is the preferred SOC the battery wants to attain? 
            -> surplus of ESS = actual SOC + aggregated supply from all devices (could be negative) - the preferred SOC 
        """
        self.surplus = self.soc_actual + self.total_supply_from_devices_at_step - self.soc_preferred
        print('soc surplus of house %d =' % self.agent.id , self.surplus)

    def soc_preferred_calc(self):
        """forecast of load minus (personal) productions over horizon expresses preferred soc of ESS"""
        # self.soc_preferred = sum(self.load_horizon) - sum(self.production_horizon)
        return

    def update_ess_state(self):
        self.soc_actual = self.soc_actual + self.balance
        assert 0 > self.soc_actual <= self.max_capacity and self.soc_actual

    def ess_physics(self):
        """ model any interesting physics applicable"""
        # such as conversion efficiency, depth of charge efficiency
        pass


class PVPanel(object):
    def __init__(self, agent, pv_data):
        """PVPanel device"""
        self.agent = agent
        self.data = [pv_data]
        self.next_interval_estimated_generation = None
        # TODO: API to PVLIB-Python?

    def get_generation(self, current_step):
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_generation = self.data[current_step]
        return self.next_interval_estimated_generation

    def uniform_call_to_device(self, current_step):
        assert current_step == self.agent.model.step_count
        print("PV of house %s checking in" % self.agent.id)
        self.next_interval_estimated_generation = self.data[current_step]  # production thus positive
        return self.next_interval_estimated_generation


class GeneralLoad(object):
    def __init__(self, agent, load_data):
        """ General load device """
        self.agent = agent
        self.data = [load_data]
        self.next_interval_estimated_load = None

    def get_load(self, current_step):
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_load = - self.data[current_step]  # load thus negative
        return self.next_interval_estimated_load

    def uniform_call_to_device(self, current_step):

        print("Load of house %s checking in" % self.agent.id)
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_load = self.get_load(current_step)
        return self.next_interval_estimated_load


class FuelCell(object):
    """ FuelCell device """

    """ 
        Electrolyzer produces hydrogen gas. This gas can either be sold 
            - to fueling HydrogenCar objects 
            - or used by a FuelCell object to produce electricity, to be sold on the energy market ]
        This class models the FuelCell 
    """
    # TODO: the second half of the electrolyzer / fuel-cell story.  RLI is responsible for this.



