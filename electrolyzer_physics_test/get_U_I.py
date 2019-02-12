# The total electrolysis voltage consists out of three different voltage parts.
# If the current isn't given an iteration is needed to get the total voltage.
import u_act
import u_ohm
import u_rev


def get_v_i(self):
    # This is the tolerance within the el. power is allowed to differ as a result of the iteration.
    relative_error = 1e-5
    # Create a dummy for the power calculated within the iteration.
    power_iteration = 0
    # Create a dummy for the voltage calculated within the iteration.
    voltage_iteration = 0
    this_temp = self.temp
    # Calculate the current density through the chemical power to start the iteration.
    # P_H2 = P_elec * eta (self.power = P_elec)
    cur_dens_iteration = (self.power * self.eta_ely * 2 * self.faraday) / (self.area_cell * self.z_cell *
                                                                           self.molarity * self.upp_heat_val)
    # Calculate the start current.
    current_iteration = cur_dens_iteration * self.area_cell

    # Determine the power deviation between the power target and the power reach within the iteration.
    power_deviation = power_iteration - self.power

    # To continue further calculations, power_deviation must always be positive
    if power_deviation < 0:
        power_deviation = power_deviation * (-1)

    # Execute the iteration until the power deviation is within the relative error which means the deviation is
    # accepted.
    while power_deviation > relative_error:
        # Calculate the voltage existing of three different parts.
        v_rev = (u_rev.ely_voltage_u_rev(self, this_temp))
        v_act = (u_act.ely_voltage_u_act(self, cur_dens_iteration, this_temp))
        v_ohm = (u_ohm.ely_voltage_u_ohm(self, cur_dens_iteration, this_temp))
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
