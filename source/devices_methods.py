import math


def ely_voltage_u_act(ely, cur_dens, temp):

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

    electrolyte_thickness = ely.fitting_value_electrolyte_thickness

    # Temperature of this loop run [K].
    this_temp = temp
    # The conductivity of the the potassium hydroxide (KOH) solution [1/(Ohm*cm)].
    conductivity_electrolyte = -2.041 * ely.molarity_KOH - 0.0028 * ely.molarity_KOH**2 + 0.001043 * \
                                ely.molarity_KOH**3 + 0.005332 * ely.molarity_KOH * this_temp + 207.2 * \
                                ely.molarity_KOH / this_temp - 0.0000003 * ely.molarity_KOH**2 * this_temp**2
    # The electrolyte resistance [Ohm*cm²].
    resistance_electrolyte = electrolyte_thickness / conductivity_electrolyte
    # Void fraction of the electrolyte (j is multiplied by 10^4 because the units the formula is made for is A/m²
    # and j is in A/cm²) [-].
    epsilon = 0.023 * 2/3 * (cur_dens * 10**4)**0.3
    # The conductivity of bubbles and other effects [1/(Ohm*cm)].
    conductivity_other = (1 - epsilon)**1.5 * conductivity_electrolyte
    # Computing the resistance of bubbles in the electrolyte and other effects [Ohm*cm²].
    resistance_other = electrolyte_thickness / conductivity_other
    # Total ohmic resistance [Ohm*cm²].
    resistance_total = resistance_electrolyte + resistance_other
    # Cell voltage loss due to ohmic resistance [V].
    # (j is the current density with the unit A/cm²).
    voltage_ohm = resistance_total * cur_dens
    return voltage_ohm


def ely_voltage_u_rev(ely, temp):
    # This calculations are valid in a temperature range from 0°C - 250°C, a pressure range from 1 bar - 200 bar and a
    # concentration range from 2 mol/kg - 18 mol/kg.

    # Coefficient 1 for the vapor pressure of the KOH solution.
    c1 = -0.0151 * ely.molality_KOH - 1.6788e-03 * ely.molarity_KOH**2 + 2.2588e-05 * ely.molality_KOH**3
    # Coefficient 2 for the vapor pressure of the KOH solution.
    c2 = 1.0 - 1.2062e-03 * ely.molality_KOH + 5.6024e-04 * ely.molality_KOH**2 - 7.8228e-06 * ely.molality_KOH**3

    '# COMPUTATION FOR ALL REQUESTED TEMPERATURES'
    # Get the temperature for this loop run [K].
    this_temp = temp
    # Compute the part of the reversible cell voltage that changes due to temperature [V].
    voltage_temperature = 1.5184 - 1.5421e-03 * this_temp + 9.526e-05 * this_temp * math.log(this_temp) + 9.84e-08 \
                           * this_temp**2
    # Calculate the vapor pressure of water [bar].
    pressure_water = math.exp(81.6179 - 7699.68 / this_temp - 10.9 * math.log(this_temp) + 9.5891e-03 * this_temp)
    # Calculate the vapor pressure of KOH solution [bar].
    pressure_koh = math.exp(2.302 * c1 + c2 * math.log(pressure_water))
    # Calculate the water activity value.
    water_activity = math.exp(-0.05192 * ely.molality_KOH + 0.003302 * ely.molality_KOH**2 + (3.177 * ely.molality_KOH -
                              2.131 * ely.molality_KOH**2) / this_temp)
    # Compute the part of the reversible cell voltage that changes due to pressure [V].
    voltage_pressure = ely.gas_const * this_temp / (ely.n * ely.faraday) * math.log((ely.pressure - pressure_koh) *
                       (ely.pressure - pressure_koh)**0.5 / water_activity)
    # Calculate the reversible voltage [V].
    voltage_reversible = voltage_temperature + voltage_pressure

    return voltage_reversible


def cell_temp(self):
    # Constant factor for temperature rise/ drop within 2.5 hours until end value.
    a = 0.0007

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
    temp_aim = self.temp_0 + (self.temp_end - self.temp_0) / (self.cur_dens_max - self.cur_dens_min) * (
                              (cur_dens_now - self.cur_dens_min))

    # Asymptotic rise/drop of the temperature.
    temp_now = temp_before + a * (temp_aim - temp_before)

    # Return temperature for this iteration step.
    return temp_now


def get_v_i(self):
    relative_error = 1e-5
    power_iteration = 0
    voltage_iteration = 0
    this_temp = self.temp
    cur_dens_iteration = (self.power * self.eta_ely * 2 * self.faraday) / (self.area_cell * self.z_cell *
                                                                           self.molarity * self.upp_heat_val)
    current_iteration = cur_dens_iteration * self.area_cell
    power_deviation = power_iteration - self.power

    if power_deviation < 0:
        power_deviation = power_deviation * (-1)

    while power_deviation > relative_error:
        v_rev = (ely_voltage_u_rev(self, this_temp))
        v_act = (ely_voltage_u_act(self, cur_dens_iteration, this_temp))
        v_ohm = (ely_voltage_u_ohm(self, cur_dens_iteration, this_temp))
        voltage_iteration = (v_rev + v_act + v_ohm) * self.z_cell
        power_iteration = voltage_iteration * current_iteration / 1000
        current_iteration = self.power / voltage_iteration * 1000
        cur_dens_iteration = current_iteration / self.area_cell

        power_deviation = power_iteration - self.power
        if power_deviation < 0:
            power_deviation = power_deviation * (-1)

    self.voltage = voltage_iteration
    self.current = current_iteration
    self.cur_dens = cur_dens_iteration
    self.power = power_iteration


