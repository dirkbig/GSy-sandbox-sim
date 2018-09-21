from source.const import *
from source.devices_methods import *
import logging
device_log = logging.getLogger('device')


class ESS(object):
    def __init__(self, agent, ess_data):
        device_log.info('ESS added to house %d', agent.id)
        super().__init__()
        self.agent = agent

        """ ESS characteristics extracted from ess_data """
        self.initial_capacity = ess_data[0]
        self.max_capacity = ess_data[1]
        self.soc_actual = self.initial_capacity * self.max_capacity
        device_log.info('soc_actual house %d = %d' % (self.agent.id , self.soc_actual))

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
        device_log.info('devices list of household %d:' % self.agent.id, self.agent.devices)

        total_supply_from_devices = 0
        for device in self.agent.devices:
            if device != 'ESS':
                total_supply_from_devices += self.agent.devices[device].uniform_call_to_device(current_step)
        self.total_supply_from_devices_at_step = total_supply_from_devices

    def uniform_call_to_device(self, current_step):
        device_log.info("ESS of house %s checking in" % self.agent.id)
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
        device_log.info('soc surplus of house %d =%d' % (self.agent.id, self.surplus))

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
        device_log.info("PV of house %s checking in" % self.agent.id)
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
        device_log.info("Load of house %s checking in" % self.agent.id)
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_load = self.get_load(current_step)
        return self.next_interval_estimated_load


class Electrolyzer(object):
    """ Electrolyzer device"""
    def __init__(self, agent, electrolyzer_data, cell_area=1500, n_cell=140, p=1.5):
        self.data = electrolyzer_data
        self.next_interval_estimated_fuel_consumption = None
        self.area_cell = cell_area
        self.z_cell = n_cell
        self.faraday = faraday
        self.gas_const = gas_const
        self.n = n
        self.molarity = molarity
        self.molarity_KOH = molarity_KOH
        self.pressure = p * pressure_factor
        self.upp_heat_val = upp_heat_val
        self.eta_ely = eta_ely

        self.fitting_value_exchange_current_density = fitting_value_exchange_current_density
        self.fitting_value_electrolyte_thickness = fitting_value_electrolyte_thickness

        """ Electrolyzer state """
        self.cur_dens = 0
        self.current = 0
        self.voltage = 0
        self.power = 0
        self.temp = temp

        self.heating_time = heating_time
        self.temp_0 = temp_0
        self.temp_end = temp_end
        self.cur_dens_max = cur_dens_max
        self.cur_dens_max_temp = cur_dens_max_temp
        self.cur_dens_min = cur_dens_min

        self.sec_counter = sec_counter
        self.cur_dens_before = self.cur_dens
        self.temp_before = self.temp

        """ Voltage variables for updating state of electrolyzer regarding power """
        self.v_rev = None
        self.v_act = None
        self.v_ohm = None

    def get_demand_electrolyzer(self, current_step):
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_fuel_consumption = - self.data[current_step]  # demand thus negative
        return self.next_interval_estimated_fuel_consumption

    def uniform_call_to_device(self, current_step):
        device_log.info("Electrolyzer of house %s checking in" % self.agent.id)
        assert current_step == self.agent.model.step_count
        self.next_interval_estimated_fuel_consumption = self.get_demand_electrolyzer(current_step)
        # this now assumes that an electrolyzer only demands electrical energy to create gas.
        # TODO: create a fuel-cell class/object that is linked to the electrolyser, using its stored gas.
        return self.next_interval_estimated_fuel_consumption

    def update_power(self, optimization_data):
        """ Updates power consumption of electrolyzer """

        """There could be a case where power or current is given from the opt data. So check which data is given"""
        if optimization_data[2] > 0 and optimization_data[3] == 0:
            """When power is provided"""
            self.power = optimization_data[2]
            get_v_i(self)

        elif optimization_data[2] == 0 and optimization_data[3] > 0:
            """If current is provided"""
            self.current = optimization_data[3]
            self.cur_dens = self.current / self.area_cell

            self.v_rev = ely_voltage_u_rev(self, self.temp)
            self.v_act = ely_voltage_u_act(self, self.cur_dens, self.temp)
            self.v_ohm = ely_voltage_u_ohm(self, self.cur_dens, self.temp)

            if self.cur_dens == 0:
                self.voltage = 0
            else:
                self.voltage = (self.v_act + self.v_rev + self.v_ohm) * self.z_cell

            self.power = self.voltage * self.current

        else:
            self.current = 0
            self.cur_dens = 0
            self.power = 0
            self.voltage = 0

        """ Updates electrolyzer temperature"""
        self.temp = cell_temp(self)


class FuelCell(object):
    """ FuelCell device """

    """ 
        Electrolyzer produces hydrogen gas. This gas can either be sold 
            - to fueling HydrogenCar objects 
            - or used by a FuelCell object to produce electricity, to be sold on the energy market ]
        This class models the FuelCell 
    """
    # TODO: the second half of the electrolyzer / fuel-cell story.  RLI is responsible for this.



