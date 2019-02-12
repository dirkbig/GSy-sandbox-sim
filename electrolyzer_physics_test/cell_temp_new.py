# This function determines the temperature of the electrolyzer.
# It uses a function to get a quasi-asymptotic rise / drop of the temperature that reaches its end value after 2.5hours.
# Highest/ Lowest temperature is reached after a certain heating/cooling time.


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
