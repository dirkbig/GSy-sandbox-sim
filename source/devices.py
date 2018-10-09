from source.const import *
from source.devices_methods import *
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
        self.min_capacity = 0.1 * self.max_capacity

        self.soc_actual = self.initial_capacity
        device_log.info('soc_actual house %d = %d' % (self.agent.id , self.soc_actual))

        """ initialization of all information the smart-ESS needs for its strategy  """
        self.next_interval_load = None
        self.next_interval_production = None
        self.next_interval_electrolyzer_load = None

        """ strategy variables """
        self.total_supply_from_devices_at_step = None
        self.soc_preferred = None
        self.surplus = None

        """ SOC forecasting """
        self.production_horizon = 0
        self.load_horizon = 0

    def update_from_household_devices(self):
        """ ask an update from all devices within the information sphere
            (this is of course, all devices within the same house """

        current_step = self.agent.model.step_count
        device_log.info('devices list of household %d:' % self.agent.id, self.agent.devices)

        total_supply_from_devices = 0
        for device in self.agent.devices:
            if device != 'ESS':
                total_supply_from_devices += self.agent.devices[device].uniform_call_to_device(current_step)

        return total_supply_from_devices

    def uniform_call_to_device(self, current_step):
        device_log.info("ESS of house %s checking in" % self.agent.id)
        self.agent.soc_actual = self.soc_actual
        return

    def update_ess_state(self, energy_influx):
        """ every time something goes in (or out) of the ESS, call this function with the energy influx as parameter """
        storage_space_left = self.max_capacity - self.soc_actual
        local_overflow = 0
        local_deficit = 0
        assert 0 <= self.soc_actual <= self.max_capacity
        assert storage_space_left >= 0

        if 0 < energy_influx < storage_space_left:
            self.soc_actual += energy_influx
            local_overflow = 0
        elif energy_influx > storage_space_left > 0:
            self.soc_actual = self.max_capacity
            local_overflow = energy_influx - storage_space_left
        elif energy_influx < 0 < self.soc_actual + energy_influx:
            self.soc_actual += energy_influx
            local_deficit = 0
        elif energy_influx < 0 and self.soc_actual + energy_influx < 0:
            self.soc_actual = 0
            local_deficit = energy_influx - self.soc_actual

        assert 0 <= self.soc_actual <= self.max_capacity

        self.agent.soc_actual = self.soc_actual
        self.agent.data.soc_list_over_time[self.agent.id][self.agent.model.step_count] = self.soc_actual
        self.agent.data.deficit_over_time[self.agent.id][self.agent.model.step_count] = local_deficit
        self.agent.data.overflow_over_time[self.agent.id][self.agent.model.step_count] = local_overflow

    @staticmethod
    def ess_physics(self):
        """ model any interesting physics applicable"""
        # TODO: RLI ESS model
        # such as conversion efficiency, depth of charge efficiency
        """ depth of charge """
        pass

    def ess_demand_calc(self, current_step):
        """calculates the demand expresses by a household's ESS"""
        total_supply_from_devices = self.update_from_household_devices()

        self.soc_preferred_calc()
        if self.soc_preferred is None:
            self.soc_preferred = 0

        """ The logic here is straight forward; what is the preferred SOC the battery wants to attain? 
            -> surplus of ESS = actual SOC + aggregated supply from all devices (could be negative) - the preferred SOC 
        """
        self.surplus = self.soc_actual + total_supply_from_devices - self.soc_preferred
        device_log.info('soc surplus of house %d = %f' % (self.agent.id, self.surplus))

    def soc_preferred_calc(self):
        """forecast of load minus (personal) productions over horizon expresses preferred soc of ESS"""
        # TODO: perfect foresight estimation of horizon
        count = self.agent.model.step_count
        """ 'Estimate' the coming X hours of load and production forecast """

        if self.agent.has_load is True:
            max_horizon = min(len(self.agent.pv_data), count + horizon)
            self.load_horizon = self.agent.load_data[count:count + max_horizon]
        else:
            self.load_horizon = [0]

        if self.agent.has_pv is True:
            max_horizon = min(len(self.agent.pv_data), count + horizon)
            self.production_horizon = self.agent.pv_data[count: max_horizon]
        else:
            self.production_horizon = [0]

        self.soc_preferred = sum(self.load_horizon) - sum(self.production_horizon)
        if self.soc_preferred < self.min_capacity:
            self.soc_preferred = self.min_capacity

        print('soc_preferred', self.soc_preferred)
        return


class PVPanel(object):
    def __init__(self, agent, pv_data):
        """PVPanel device"""
        self.agent = agent
        self.device_pv_data = pv_data
        self.next_interval_estimated_generation = None
        # TODO: API to PVLIB-Python?

    def get_generation(self, current_step):

        self.next_interval_estimated_generation = float(self.device_pv_data[current_step])
        if self.next_interval_estimated_generation is None:
            self.next_interval_estimated_generation = 0

        return self.next_interval_estimated_generation

    def uniform_call_to_device(self, current_step):
        assert current_step == self.agent.model.step_count
        device_log.info("PV of house %s checking in" % self.agent.id)
        self.next_interval_estimated_generation = self.get_generation(current_step)  # production thus positive

        return self.next_interval_estimated_generation


class GeneralLoad(object):
    def __init__(self, agent, load_data):
        """ General load device """
        self.agent = agent
        self.device_load_data = load_data
        self.next_interval_estimated_load = None

    def get_load(self, current_step):
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_load = - float(self.agent.load_data[current_step])  # load thus negative
        if self.next_interval_estimated_load is None:
            self.next_interval_estimated_load = 0

        return self.next_interval_estimated_load

    def uniform_call_to_device(self, current_step):
        device_log.info("Load of house %s checking in" % self.agent.id)
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




