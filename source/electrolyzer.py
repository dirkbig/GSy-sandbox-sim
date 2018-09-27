from source.const import *
import math
import warnings
from mesa import Agent
import source.const as const
import logging
electrolyzer_log = logging.getLogger("electrolyzer")


class Electrolyzer(Agent):
    """ Electrolyzer agents are created through this class """
    def __init__(self, _unique_id, model):
        super().__init__(_unique_id, self)
        electrolyzer_log.info('agent%d created', _unique_id)

        self.id = _unique_id
        self.model = model
        # Simulation time [min].
        self.sim_time = self.model.data.market_interval

        # States of the electrolyzer.
        # Current density (i = I/A) in [A / cm^2]
        self.cur_dens = 0
        # current in [A]
        self.current = 0
        # voltage in [V]
        self.voltage = 0
        # power in [kW]
        self.power = 0
        # temperature in [K]
        self.temp = ambient_temp

        # Parameters for the hydrogen station.
        # Amount of (usable) hydrogen stored [kg].
        self.stored_hydrogen = 0
        # Max. amount of (usable) hydrogen stored [kg].
        self.storage_size = const.hrs_storage_size
        # Tracker for the hydrogen demand that couldn't be fulfilled [kg].
        self.demand_not_fulfilled = 0

        # Parameter for the electrolyzer
        # size of cell surface [cm²].
        self.area_cell = 1500
        # Number of cell amount on one stack.
        self.z_cell = 140
        # Faraday constant F [As/mol].
        self.faraday = 96485
        # Gas constant R [J /(mol K)].
        self.gas_const = 8.3144621
        # Moles of electrons needed to produce a mole of hydrogen[-].
        self.n = 2
        # Molar mass M_H2 [g / mol].
        self.molarity = 2.01588
        # Molar concentration of the KOH solution (10 mol/l for 28 wt% KOH) [mol/l].
        self.molarity_KOH = 10
        # Molal concentration of the KOH solution (7.64 mol/kg for 30 wt% KOH) [mol/kg].
        self.molality_KOH = 7.64
        # pressure of hydrogen in the system in [Pa]
        self.pressure = 40 * 10**5
        # upper heating value in [MJ / kg]
        self.upp_heat_val = 141.8
        # efficiency of the electrolysis system (efficiency factor between H2 power and elects. power)
        self.eta_ely = 0.65

        # The fitting parameter exchange current density[A / cm²].
        self.fitting_value_exchange_current_density = 1.4043839e-3
        # The thickness of the electrolyte layer [cm].
        self.fitting_value_electrolyte_thickness = 0.2743715938

        # Min. temperature of the electrolyzer (completely cooled down) in [K]
        self.temp_min = 293.15
        # highest temperature the electrolyzer can be in [K]
        self.temp_max = 353.15
        # maximal current density given by the manufacturer in [A/cm^2]
        self.cur_dens_max = 0.4
        # at this current density the maximal temperature is reached in [A/cm^2]
        self.cur_dens_max_temp = 0.35

        # counts the number of seconds the simulation is running
        self.sec_counter = 1
        # saves last value of current density
        self.cur_dens_before = self.cur_dens
        # saves last temperature value
        self.temp_before = self.temp

    def pre_auction_round(self):
        pass

    def post_auction_round(self):
        pass

    def update_storage(self):
        # Update the mass of the hydrogen stored.
        mass_old = self.stored_hydrogen
        mass_produced = self.current * self.z_cell / (2 * self.faraday) * self.molarity
        # HAS TO BE READ VIA THE TIMESERIES !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        mass_demanded = 0
        # Update the mass in the storage
        self.stored_hydrogen = mass_old + mass_produced - mass_demanded
        # Check if hydrogen demand could't be fulfilled. If so, track it and set the storage to empty.
        if self.stored_hydrogen < 0:
            self.demand_not_fulfilled += abs(self.stored_hydrogen)
            self.stored_hydrogen = 0

    # Determine new measurement data for next step.
    def update_power(self, new_power_value):
        # Update the power value within the physical limits of the electrolyzer.
        # Parameter:
        #  new_power_value: Power value for the next time step [kW].

        self.power = new_power_value
        # Update voltage, current, current density and power in an iterative process.
        self.get_v_i()
        # Check if the current density is above the max. allowed value.
        if self.cur_dens > self.cur_dens_max:
            warnings.warn("Electrolyzer bought more electricity than it can use.")
            # Update current density to max. allowed value
            self.cur_dens = self.cur_dens_max
            # Calculate the current.
            self.current = self.cur_dens * self.area_cell

            # Calculate the three parts the voltage consists of.
            v_rev = self.ely_voltage_u_rev(self.temp)
            v_act = self.ely_voltage_u_act(self.cur_dens, self.temp)
            v_ohm = self.ely_voltage_u_ohm(self.cur_dens, self.temp)

            # Calculate the total voltage.
            if self.cur_dens == 0:
                # If there are numeric deviation because of the value 0 set the voltage to the value 0.
                self.voltage = 0
            else:
                # Calculate the voltage [V].
                self.voltage = (v_act + v_rev + v_ohm) * self.z_cell

            # Calculate the power [kW].
            self.power = self.voltage * self.current / 1000

        # Calculate the temperature.
        self.temp = self.cell_temp()

    def cell_temp(self):
        # Calculate the electrolyzer temperature for the next time step.

        # Check if current density is higher than the given density at the highest possible temperature. If so,
        # set the current density to its maximum.
        if self.cur_dens > self.cur_dens_max_temp:
            cur_dens_now = self.cur_dens_max_temp
        else:
            cur_dens_now = self.cur_dens

        # Save the temperature calculated one step before.
        temp_before = self.temp

        # Calculate the temperature to which the electrolyzer is heating up depending on the given current density.
        # Lin. interpolation
        temp_aim = self.temp_min + (self.temp_max - self.temp_min) * cur_dens_now / self.cur_dens_max_temp

        # Calculate the new temperature of the electrolyzer by Newtons law of cooling. The exponent (-t[s]/2310) was
        # parameterized such that the 98 % of the temperature change are reached after 2.5 hours.
        temp_new = temp_aim + (temp_before - temp_aim) * math.exp(-self.sim_time*60 / 2310)

        # Return the new electrolyzer temperature [K].
        return temp_new

    def get_v_i(self):
        # The total electrolysis voltage consists out of three different voltage parts (u_act, u_ohm, u_ref).
        # If the current isn't given an iteration is needed to get the total voltage.
        # This is the tolerance within the el. power is allowed to differ as a result of the iteration.
        relative_error = 1e-5
        # Create a dummy for the power calculated within the iteration.
        power_iteration = 0
        # Create a dummy for the voltage calculated within the iteration.
        voltage_iteration = 0
        this_temp = self.temp
        # Calculate the current density through the chemical power to start the iteration.
        # P_H2 = P_elec * eta (self.power = P_elec)
        cur_dens_iteration = (self.power * self.eta_ely * 2.0 * self.faraday) / (self.area_cell * self.z_cell *
                                                                               self.molarity * self.upp_heat_val)
        # Calculate the start current.
        current_iteration = cur_dens_iteration * self.area_cell

        # Determine the power deviation between the power target and the power reach within the iteration.
        power_deviation = abs(power_iteration - self.power)

        # Execute the iteration until the power deviation is within the relative error which means the deviation is
        # accepted.
        while power_deviation > relative_error:
            # Calculate the voltage existing of three different parts.
            v_rev = (self.ely_voltage_u_rev(this_temp))
            v_act = (self.ely_voltage_u_act(cur_dens_iteration, this_temp))
            v_ohm = (self.ely_voltage_u_ohm(cur_dens_iteration, this_temp))
            # Get the voltage for this iteration step.
            voltage_iteration = (v_rev + v_act + v_ohm) * self.z_cell
            # Get the power for this iteration step.
            power_iteration = voltage_iteration * current_iteration / 1000
            # Get the current for this iteration step.
            current_iteration = self.power / voltage_iteration * 1000
            # Get the current density for this iteration step.
            cur_dens_iteration = current_iteration / self.area_cell

            # Calculate the new power deviation.
            power_deviation = power_iteration - self.power
            if power_deviation < 0:
                power_deviation = power_deviation * (-1)

        # Save the final values.
        self.voltage = voltage_iteration
        self.current = current_iteration
        self.cur_dens = cur_dens_iteration
        self.power = power_iteration

    def ely_voltage_u_act(ely, cur_dens, temp):
        # This voltage part describes the activity losses within the electolyser.
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)!

        j0 = ely.fitting_value_exchange_current_density

        '# COMPUTATION FOR EACH NODE'
        # The temperature of this loop run[K].
        this_temp = temp
        # The "alpha" values are valid for Ni - based electrodes.
        alpha_a = 0.0675 + 0.00095 * this_temp
        alpha_c = 0.1175 + 0.00095 * this_temp
        # The two parts of the activation voltage for this node[V].
        u_act_a = 2.306 * (ely.gas_const * this_temp) / (ely.n * ely.faraday * alpha_a) * math.log10(cur_dens / j0)
        u_act_c = 2.306 * (ely.gas_const * this_temp) / (ely.n * ely.faraday * alpha_c) * math.log10(cur_dens / j0)
        # The activation voltage for this node[V].
        voltage_activation = u_act_a + u_act_c

        return voltage_activation

    def ely_voltage_u_ohm(ely, cur_dens, temp):
        # This model takes into account two ohmic losses, one being the resistance of the electrolyte itself
        # (resistanceElectrolyte) and other losses like the presence of bubbles (resistanceOther).
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)

        electrolyte_thickness = ely.fitting_value_electrolyte_thickness

        # Temperature of this loop run [K].
        this_temp = temp
        # The conductivity of the the potassium hydroxide (KOH) solution [1/(Ohm*cm)].
        conductivity_electrolyte = -2.041 * ely.molarity_KOH - 0.0028 * ely.molarity_KOH ** 2 + 0.001043 * \
                                   ely.molarity_KOH ** 3 + 0.005332 * ely.molarity_KOH * this_temp + 207.2 * \
                                   ely.molarity_KOH / this_temp - 0.0000003 * ely.molarity_KOH ** 2 * this_temp ** 2
        # The electrolyte resistance [Ohm*cm²].
        resistance_electrolyte = electrolyte_thickness / conductivity_electrolyte
        # Void fraction of the electrolyte (j is multiplied by 10^4 because the units the formula is made for is A/m²
        # and j is in A/cm²) [-].
        epsilon = 0.023 * 2 / 3 * (cur_dens * 10 ** 4) ** 0.3
        # The conductivity of bubbles and other effects [1/(Ohm*cm)].
        conductivity_other = (1 - epsilon) ** 1.5 * conductivity_electrolyte
        # Computing the resistance of bubbles in the electrolyte and other effects [Ohm*cm²].
        resistance_other = electrolyte_thickness / conductivity_other
        # Total ohmic resistance [Ohm*cm²].
        resistance_total = resistance_electrolyte + resistance_other
        # Cell voltage loss due to ohmic resistance [V].
        # (j is the current density with the unit A/cm²).
        voltage_ohm = resistance_total * cur_dens
        return voltage_ohm

    def ely_voltage_u_rev(self, temp):
        # The reversible voltage can be calculated by two parts, one takes into account changes of the reversible cell
        # voltage due to temperature changes, the second part due to pressure changes.
        # Source: 'Modeling an alkaline electrolysis cell through reduced-order and loss estimate approaches'
        # from Milewski et al. (2014)
        # This calculations are valid in a temperature range from 0°C - 250°C, a pressure range from 1 bar - 200 bar and
        # a concentration range from 2 mol/kg - 18 mol/kg.

        # Coefficient 1 for the vapor pressure of the KOH solution.
        c1 = -0.0151 * self.molality_KOH - 1.6788e-03 * self.molarity_KOH ** 2 + 2.2588e-05 * self.molality_KOH ** 3
        # Coefficient 2 for the vapor pressure of the KOH solution.
        c2 = 1.0 - 1.2062e-03 * self.molality_KOH + 5.6024e-04 * self.molality_KOH ** 2 - 7.8228e-06 * self.molality_KOH**3

        '# COMPUTATION FOR ALL REQUESTED TEMPERATURES'
        # Get the temperature for this loop run [K].
        this_temp = temp
        # Compute the part of the reversible cell voltage that changes due to temperature [V].
        voltage_temperature = 1.5184 - 1.5421e-03 * this_temp + 9.526e-05 * this_temp * math.log(this_temp) + 9.84e-08 \
                              * this_temp ** 2
        # Calculate the vapor pressure of water [bar].
        pressure_water = math.exp(81.6179 - 7699.68 / this_temp - 10.9 * math.log(this_temp) + 9.5891e-03 * this_temp)
        # Calculate the vapor pressure of KOH solution [bar].
        pressure_koh = math.exp(2.302 * c1 + c2 * math.log(pressure_water))
        # Calculate the water activity value.
        water_activity = math.exp(
            -0.05192 * self.molality_KOH + 0.003302 * self.molality_KOH ** 2 + (3.177 * self.molality_KOH -
                                                                            2.131 * self.molality_KOH ** 2) / this_temp)
        # Compute the part of the reversible cell voltage that changes due to pressure [V].
        voltage_pressure = self.gas_const * this_temp / (self.n * self.faraday) *\
                    math.log((self.pressure - pressure_koh) * (self.pressure - pressure_koh) ** 0.5 / water_activity)
        # Calculate the reversible voltage [V].
        voltage_reversible = voltage_temperature + voltage_pressure

        return voltage_reversible


""" Stand alone testing of the Electrolyzer device"""
if __name__ == "__main__":
    Ely = Electrolyzer(1, [])

    for i_timestep in range(20):
        ely_voltage = 190

        Ely.update_power(ely_voltage)
        Ely.update_storage()

        print("Time step {:3.0f}; time passed {:4.0f} min; Ely power {:.2f} kW; Voltage {:.2f} V; Ely current {:.2f}"
              " A; Current density {:.4f} A/cm²; Stored mass {:6.2f} kg; Temp: {:.2f}".format(
                i_timestep, i_timestep*const.market_interval, Ely.power, Ely.voltage,
                Ely.current, Ely.cur_dens, Ely.stored_hydrogen, Ely.temp))


