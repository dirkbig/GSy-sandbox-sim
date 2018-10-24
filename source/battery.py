from mesa import Agent
import source.const as const
from math import exp
import warnings
import logging

""" 
The battery model takes into account charging and discharging efficiencies. 
Also the battery aging is considered according to:
    A holistic aging model for Li(NiMnCo)O2 based 18650 lithium-ion batteries
    Johannes Schmalstieg, Stefan Käbitz, Madeleine Ecker, Dirk Uwe Sauer
    2014
    https://www.sciencedirect.com/science/article/abs/pii/S0378775314001876
The aging includes time, voltage and temperature calendar aging and a cycling aging.  
Aging effects are converted to financial loss and taken into account for the bidding strategy.
"""

battery_log = logging.getLogger("battery")

class Battery(Agent):
    """ Battery agents are created through this class """
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        battery_log.info('agent%d (battery) created', _unique_id)

        self.id = _unique_id
        self.model = model
        # Interval time [min].
        self.interval_time = const.market_interval

        # Physical parameter
        # Capacity [kWh]
        self.capacity_init = 100
        self.capacity = self.capacity_init
        # Stored electricity [kWh].
        self.stored_electricity = 0
        # Charging and discharging efficiency (0 -> 0 %, 1 -> 100 %).
        self.charge_eff = 0.9
        self.discharge_eff = 0.9
        # C rate (how much of capacity can be charged/discharged per hour, 1 -> 100 %).
        self.c_rate = 1
        # Nominal battery cell voltage [V].
        self.cell_voltage = 3.6
        # Nominal capacity of one single battery cell [Ah].
        self.cell_capacity = 2.05
        # Availability for discharge delta DOD (1 is 100% of capacity is available).
        self.delta_dod = 1
        # Time the battery is in use [d].
        self.time_in_use = 0
        # Total charge throughput Q [Ah].
        self.total_charge_throughput = 0




    def pre_auction_round(self):
        pass


    def update_state(self, charging_energy, temperature=273.15+50):
        """
        Update the states of the battery (state of charge and max. capacity, which decreases due to aging).

        :param charging_energy: The amount of electricity received (pos) or distributed (neg) [kWh].
        :param temperature: The battery temperature [K]
        """

        # Check if received energy is within physical limits, otherwise correct that value.
        [max_charge, max_discharge] = self.get_charging_limit()
        if charging_energy < -max_discharge:
            warnings.warn("Discharge below the level physically possible tried.")
            charging_energy = -max_discharge
        elif charging_energy > max_charge:
            warnings.warn("Charge above the level physically possible tried.")
            charging_energy = max_charge

        # Update the state of charge.
        if charging_energy < 0:
            # Case: Discharge the battery. Calculate the new stored electricity [kWh].
            self.stored_electricity += charging_energy / self.discharge_eff
            dod = -charging_energy / self.discharge_eff / self.capacity
        elif charging_energy > 0:
            # Case: Charging the battery. Calculate the new stored electricity [kWh].
            self.stored_electricity += charging_energy * self.charge_eff
            dod = charging_energy * self.charge_eff / self.capacity
        else:
            dod = 0
        # calculate total charge throughput Q

        self.total_charge_throughput += self.cell_capacity * dod
        # Update the capacity due to aging [kWh].
        capacity_loss_rel = self.get_capacity_loss_by_aging(temperature)
        self.capacity = (1 - capacity_loss_rel) * self.capacity_init

        if self.stored_electricity > self.capacity:
            self.stored_electricity = self.capacity

        # Update the time the battery was used [d].
        self.time_in_use += self.interval_time / 60 / 24
        battery_log.info("Battery states updated. Capacity loss due to aging is {} kWh.".format(capacity_loss_rel))


        # ########################################################################
        """
        # Check if received energy is within physical limits, otherwise correct that value.
        [max_charge, max_discharge] = self.get_charging_limit()
        if charging_energy < -max_discharge:
            warnings.warn("Discharge below the level physically possible tried.")
            charging_energy = -max_discharge
        elif charging_energy > max_charge:
            warnings.warn("Charge above the level physically possible tried.")
            charging_energy = max_charge

        # Update the state of charge.
        if charging_energy < 0:
            # Case: Discharge the battery. Calculate the new stored electricity [kWh].
            self.stored_electricity += charging_energy / self.discharge_eff
            dod = -charging_energy / self.discharge_eff / self.capacity
        elif charging_energy > 0:
            # Case: Charging the battery. Calculate the new stored electricity [kWh].
            self.stored_electricity += charging_energy * self.charge_eff
            dod = charging_energy * self.charge_eff / self.capacity
        else:
            dod = 0

        # Update the capacity due to aging [kWh].
        capacity_loss = self.get_capacity_loss_by_aging(273.15+10, dod)
        self.capacity -= capacity_loss
        if self.stored_electricity > self.capacity:
            self.stored_electricity = self.capacity

        battery_log.info("Battery states updated. Capacity loss due to aging is {} kWh.".format(capacity_loss))
        """



    def get_charging_limit(self):
        # Calculates how much energy can max. be bought or distributed in the next time step.
        # Output: array [max. bought, max. distributed] in kWh.

        # Calculate the two limits for discharging: 1. stored energy, 2. C-rate limit [kWh].
        max_discharge_stored = self.stored_electricity * self.discharge_eff
        max_discharge_c_rate = self.capacity * self.c_rate * self.interval_time / 60 * self.discharge_eff
        # Max. amount of energy that can be distributed for the next step [kWh].
        max_distributed = min(max_discharge_stored, max_discharge_c_rate)

        max_charge_stored = (self.capacity - self.stored_electricity) / self.charge_eff
        max_charge_c_rate = self.capacity * self.c_rate * self.interval_time / 60 / self.charge_eff
        max_bought = min(max_charge_stored, max_charge_c_rate)

        return [max_bought, max_distributed]

    def get_capacity_loss_by_aging(self, temperature, dod, voltage=None):
        """
        Get the amount of capacity lost due to operation (cycle aging) and time (calendar aging) [kWh].

        The model equations are implemented according to:
            A holistic aging model for Li(NiMnCo)O2 based 18650 lithium-ion batteries
            Johannes Schmalstieg, Stefan Käbitz, Madeleine Ecker, Dirk Uwe Sauer
            2014
            https://www.sciencedirect.com/science/article/abs/pii/S0378775314001876

        :param voltage: Cell voltage [V]
        :param dod: depth of discharge (how much the battery has been charged or discharged, 1 being 100 %) [-]
        :param temperature: Battery temperature [K]
        :return capacity_loss: Loss of the battery capacity by aging in this time step [kWh]
        """
        # In case the cell voltage was not set, use the cell voltage parameter.
        if voltage is None:
            voltage = self.cell_voltage

        # Value considering the aging by calendar.
        alpha = (7.543 * voltage - 23.75) * 10**6 * exp(-6976/temperature)
        # Value to consider the aging by cycle (delta_dod is how much of the battery is available for discharge).
        delta_dod = 1
        beta = 7.348 * 10**-3 * (voltage - 3.667)**2 + 7.6 * 10**-4 + 4.081 * 10**-3 * delta_dod

        # Calculate the relative capacity loss (1 being 100 %).
        capacity_loss_rel = alpha * (self.interval_time / 60 / 24) ** 0.75 + \
            beta * (self.cell_capacity * dod / self.cell_voltage)**0.5
        # Return the total capacity loss [kWh].
        return capacity_loss_rel * self.capacity


if __name__ == "__main__":
    model_dummy = []
    unique_id = 1
    battery = Battery(unique_id, model_dummy)
    charge_rate = 0
    for i_step in range(96*365):
        battery.update_state(charge_rate)
        if battery.capacity == battery.stored_electricity or battery.stored_electricity == 0:
            # If the battery is full or empty, change from charging to discharging or vice versa.
            charge_rate *= -1

        if i_step % 100 == 0:
            print("Step {}: Battery states updated. Stored energy {:2} kWh, Capacity of battery is {:.5} kWh.".format(i_step, battery.stored_electricity, battery.capacity))

