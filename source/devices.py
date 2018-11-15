from math import exp
from source.const import *
from source.devices_methods import *
import source.const as const

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

        """ physics """
        # Charging and discharging efficiency (0 -> 0 %, 1 -> 100 %).
        self.charge_eff = 0.98
        self.discharge_eff = 0.98
        # C rate (how much of capacity can be charged/discharged per hour, 1 -> 100 %).
        self.c_rate = 1
        # Nominal battery cell voltage [V].
        self.cell_voltage = 3.6
        # Nominal capacity of one single battery cell [Ah].
        self.cell_capacity = 2.05
        # Availability for discharge delta DOD (1 is 100% of capacity is available).
        self.delta_dod = 0.01
        # Time the battery is in use [d].
        self.time_in_use = 0
        # Total charge throughput Q [Ah].
        self.total_charge_throughput = 0
        # Track the temperature of the different time steps [K].
        self.temperature = []

        # charging limits
        self.max_in = None
        self.max_out = None

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

    """ battery model """
    def get_charging_limit(self):

        if constraints_setting is 'on':
            # Calculates how much energy can max. be bought or distributed in the next time step.
            # Output: array [max. bought, max. distributed] in kWh.

            # Calculate the two limits for discharging: 1. stored energy, 2. C-rate limit [kWh].
            max_discharge_stored = self.soc_actual * self.discharge_eff
            max_discharge_c_rate = self.max_capacity * self.c_rate \
                                   * self.agent.data.market_interval / 60 * self.discharge_eff
            # Max. amount of energy that can be distributed for the next step [kWh].
            max_sold = min(max_discharge_stored, max_discharge_c_rate)

            max_charge_stored = (self.max_capacity - self.soc_actual) / self.charge_eff
            max_charge_c_rate = self.max_capacity * self.c_rate * self.agent.data.market_interval / 60 / self.charge_eff
            max_bought = min(max_charge_stored, max_charge_c_rate)
            print(max_bought, max_sold)
        else:
            # relaxing of constraints gimmick
            max_bought = 10000
            max_sold = 10000

        return max_bought, max_sold

    def get_capacity_loss_by_aging(self, voltage=None):
        """
        Get the amount of capacity lost due to operation (cycle aging) and time (calendar aging) [kWh].
        The model equations are implemented according to:
            A holistic aging model for Li(NiMnCo)O2 based 18650 lithium-ion batteries
            Johannes Schmalstieg, Stefan Käbitz, Madeleine Ecker, Dirk Uwe Sauer
            2014
            https://www.sciencedirect.com/science/article/abs/pii/S0378775314001876
        :param voltage: Cell voltage [V]
        :return capacity_loss: Loss of the battery capacity by aging in this time step [kWh]
        """

        # In case the cell voltage was not set, use the cell voltage parameter.
        if voltage is None:
            voltage = self.cell_voltage

        # Calculate the average temperature [K]
        avg_temperature = sum(self.temperature) / len(self.temperature)
        # Value considering the aging by calendar.
        alpha = (7.543 * voltage - 23.75) * 10**6 * exp(-6976/avg_temperature)
        capacity_loss_aging = alpha * self.time_in_use ** 0.75
        # Value to consider the aging by cycle
        beta = 7.348 * 10**-3 * (voltage - 3.667)**2 + 7.6 * 10**-4 + 4.081 * 10**-3 * self.delta_dod
        capacity_loss_charge = beta * self.total_charge_throughput**0.5
        # Calculate the relative capacity loss (1 being 100 %).
        capacity_loss_rel = capacity_loss_aging + capacity_loss_charge
        # Return relative capacity loss (1 is 100% loss).
        return capacity_loss_rel

    @staticmethod
    def get_ess_temperature(self, temperature=273.15+10):
        """ here ESS temperature model can go """
        # TODO: add this physics
        return temperature

    def update_ess_state(self, energy_influx):
        """ every time something goes in (or out) of the ESS, call this function with the energy influx as parameter """

        """ independent charging limits check 
            should be done at bidding strategy as well
        """
        temperature = self.get_ess_temperature(self)
        self.temperature.append(temperature)
        [max_charge, max_discharge] = self.get_charging_limit()

        if energy_influx < -max_discharge:
            device_log.warning("Discharge below the level physically possible tried")
            energy_influx = -max_discharge
        elif energy_influx > max_charge:
            device_log.warning("Charge above the level physically possible tried")
            energy_influx = max_charge

        storage_space_left = self.max_capacity - self.soc_actual
        local_overflow = 0
        local_deficit = 0

        try:
            assert 0 <= self.soc_actual <= self.max_capacity
            assert storage_space_left >= 0
        except AssertionError:
            device_log.error("SOC is higher than max capacity of ESS, or negative")

        # Update the state of charge.
        if 0 < energy_influx * self.charge_eff < storage_space_left:
            """ charging without overflow """
            abs_throughput = energy_influx * self.discharge_eff
            rel_throughput = abs_throughput / self.max_capacity
            self.soc_actual += abs_throughput

        elif energy_influx * self.charge_eff > storage_space_left > 0:
            """ charging with overflow """
            abs_throughput = storage_space_left
            rel_throughput = abs_throughput / self.max_capacity
            self.soc_actual = self.max_capacity

            local_overflow = abs(energy_influx) - storage_space_left

        elif energy_influx * self.discharge_eff < 0 < self.soc_actual + energy_influx:
            """ discharging without depletion """
            abs_throughput = energy_influx * self.discharge_eff
            rel_throughput = abs_throughput / self.max_capacity
            self.soc_actual += abs_throughput

        elif energy_influx * self.discharge_eff < 0 and self.soc_actual + \
                energy_influx * self.discharge_eff < 0:
            """ discharging with depletion """
            abs_throughput = self.soc_actual
            rel_throughput = abs_throughput / self.max_capacity
            self.soc_actual = 0
            local_deficit = abs(energy_influx) - self.soc_actual
        else:
            rel_throughput = 0

        try:
            assert 0 <= self.soc_actual <= self.max_capacity
            assert local_overflow == 0 or local_deficit == 0
        except AssertionError:
            device_log.error("SOC is higher than max capacity of ESS, or ESS builds up deficits/overflows")

        """ Aging of battery """
        # calculate total charge throughput Q
        self.total_charge_throughput += abs(self.cell_capacity * rel_throughput)
        # Update the capacity due to aging [kWh].
        capacity_loss_rel = self.get_capacity_loss_by_aging()
        self.max_capacity = (1 - capacity_loss_rel) * self.max_capacity

        if self.soc_actual > self.max_capacity:
            self.soc_actual = self.max_capacity

        # Update the time the battery was used [d].
        self.time_in_use += self.agent.data.market_interval / 60 / 24
        device_log.info("Battery states updated. Capacity loss due to aging is {} kWh.".format(capacity_loss_rel))

        self.agent.soc_actual = self.soc_actual
        self.agent.data.soc_list_over_time[self.agent.id][self.agent.model.step_count] = self.soc_actual
        return local_overflow, local_deficit

    """ needed for storage strategy """
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
            max_horizon = min(len(self.agent.load_data), count + horizon)
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


