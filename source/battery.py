from mesa import Agent
import source.const as const
from source.wallet import Wallet
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
        self.current_step = 0

        """ Trading. """
        self.bidding_solver = "dummy"
        self.wallet = Wallet(_unique_id)
        self.trading_state = None
        # Bid in the format [price, quantity, self ID]
        self.bid = None
        self.offer = None
        self.sold_energy = None
        self.bought_energy = None

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
        # Nominal (initial) capacity of one single battery cell [Ah].
        self.cell_capacity_init = 2.05
        # Availability for discharge delta DOD (1 is 100% of capacity is available).
        self.delta_dod = 1
        # Time the battery is in use [d].
        self.time_in_use = 0
        # Total charge throughput Q [Ah].
        self.total_charge_throughput = 0
        # Track the temperature of the different time steps [K].
        self.temperature = []

    def pre_auction_round(self):
        # Update the current time step.
        self.current_step = self.model.step_count

        self.update_bid()

    def post_auction_round(self):
        pass

    def update_bid(self):
        # Define the number of steps the perfect foresight optimization should look in the future.
        n_step = 5

        if self.bidding_solver == 'linprog':
            """ Linear program """
            # To derive the bid for this time step, a linear optimization (linprog) determines the optimal amount of
            # electricity that should be stored or sold. The basis of the optimization is the grid electricity price and
            # the storage charging and discharging efficiency.
            #
            # The optimization problem is formulated in the way:
            # min  c * x
            # s.t. A * x <= b
            # x >= 0 and x < max. producible hydrogen
            #
            # Here, x is a vector with the amount of electricity charged and another set of x for the values of
            # discharged energy, c is the estimated cost function for each time step (EEX spot marked costs are used),
            # A * x <= b is used to make sure that the storage never goes below empty or above full.
            # Number of time steps of the future used for the optimization.
            #
            # NOTE: Charging and discharging for each time step are two separated x values and they are referring to the
            # energy bought or sold to the energy system. Hereby charging values are positive and discharging values are
            # negative
            # e.g. for 3 time steps the x vector looks like this:
            # x = [x_1, x_2, x_3, x_4, x_5, x_6]
            # The indices 1-3 are for charging (>= 0), the indices 4-6 are for discharging (<= 0).

            from cvxopt import matrix, solvers
            import numpy as np

            # To be able to account for charging and discharging efficiencies, there are separated x values for charging
            # and discharging. The cost values are set accordingly.
            electricity_cost = self.model.data.utility_pricing_profile[self.current_step:self.current_step+n_step]
            c_charge = electricity_cost[:] / self.charge_eff
            c_discharge = electricity_cost[:] * self.discharge_eff
            c = np.concatenate((c_charge, c_discharge))

            # Using the inequality constraints first to make sure that the battery is never below empty or above full.
            # Further it is made sure that charging speeds are not violated. A little example for three time steps
            # forecast would look like this:
            #
            #               A           *x <=        b
            #
            #       [ C  0  0  0  0  0]       [Capacity_init - SoC_init]  \
            #       [ C  C  0  D  0  0]       [Capacity_init - SoC_init]   |-> 1. Ensure storage is never above full
            #       [ C  C  C  D  D  0]       [Capacity_init - SoC_init]  /
            #       [ 0  0  0 -D  0  0]       [SoC_init]   |-> 2. Ensure storage is never below empty
            #       [-C  0  0 -D -D  0]       [SoC_init]   |-> 2. Ensure storage is never below empty
            #       [-C -C -C -D -D -D]       [0]          |-> 3. Ensure storage SoC at the end is not below SoC_init
            #       [ C  0  0  0  0  0]       [C*cap_init*interval_time/60min]  \
            #       [ 0  C  0  0  0  0]       [C*cap_init*interval_time/60min]   |-> 4. Ensure C rate charging
            #       [ 0  0  C  0  0  0]       [C*cap_init*interval_time/60min]  /           not violated
            #       [ 0  0  0 -D  0  0] *x <= [C*cap_init*interval_time/60min]  \
            #       [ 0  0  0  0 -D  0]       [C*cap_init*interval_time/60min]   |-> 5. Ensure C rate discharging
            #       [ 0  0  0  0  0 -D]       [C*cap_init*interval_time/60min]  /           not violated
            #       [-C  0  0  0  0  0]       [0]  \
            #       [ 0 -C  0  0  0  0]       [0]   |-> 6. Ensure charging value not below 0
            #       [ 0  0 -C  0  0  0]       [0]  /
            #       [ 0  0  0  D  0  0]       [0]  \
            #       [ 0  0  0  0  D  0]       [0]   |-> 7. Ensure discharging value not above 0
            #       [ 0  0  0  0  0  D]       [0]  /
            #
            #   C: Factor charging efficiency = self.charge_eff
            #   D: Factor discharging efficiency = 1 / self.discharge_eff
            #   x: Vector of charging and discharging for each time step (in this example 3 time steps):
            #      x = [charge_ts1, charge_ts2, charge_ts3, discharge_ts1, discharge_ts2, discharge_ts3]

            C = self.charge_eff
            D = 1 / self.discharge_eff

            # OK, so let's start and define A.
            # 1. First ensure that the storage is never above full.
            A = [[C] * (i + 1) + [0.0] * (n_step - i - 1) + [D] * i + [0.0] * (n_step - i)
                 for i in range(n_step)]
            # 2. Then ensure that the storage is never below empty.
            A += [[-C] * i + [0.0] * (n_step - i) + [-D] * (i + 1) + [0.0] * (n_step - i - 1)
                  for i in range(n_step-1)]
            # 3. Then ensure that the state of charge at the end of the simulation is not below the initial SoC.
            A += [[-C] * n_step + [-D] * n_step]
            # 4. Then ensure that charging speed doesn't violate the c-rate constraint.
            A += [[0.0] * i + [C] + [0.0] * (2 * n_step - i - 1) for i in range(n_step)]
            # 5. Then ensure that discharging speed doesn't violate the c-rate constraint.
            A += [[0.0] * (n_step + i) + [-D] + [0.0] * (n_step - i - 1) for i in range(n_step)]
            # 6. Then ensure that charging cannot be negative.
            A += [[0.0] * i + [-C] + [0.0] * (2 * n_step - i - 1) for i in range(n_step)]
            # 7. Finally ensure that discharging cannot be positive.
            A += [[0.0] * (n_step + i) + [D] + [0.0] * (n_step - i - 1) for i in range(n_step)]

            # Now b can be defined.
            # 1.
            b = [self.capacity_init - self.stored_electricity] * n_step
            # 2.
            b += [self.stored_electricity] * (n_step - 1)
            # 3.
            b += [0]
            # 4. & 5.
            b += [self.c_rate * self.capacity_init * self.interval_time / 60] * n_step * 2
            # 6. & 7.
            b += [0] * n_step * 2

            # Starting the optimization process.
            # First bring c, A and b to the matrix format of the package cvxopt.
            A = matrix(np.array(A).T.tolist())
            b = matrix(b)
            c = matrix(c)
            # Silence the optimizer output.
            solvers.options['show_progress'] = False
            # Execute the optimization.
            sol = solvers.lp(c, A, b)
            print('Optimization finished: ')
            # Add up charging and discharging to get the actual charging.
            res = []
            for i in range(n_step):
                res.append(sol['x'][i] + sol['x'][i + n_step])

            print(res)
            # Return the power value needed for the optimized production and the price [kW, EUR/kWh]

        elif self.bidding_solver == 'dummy':
            res = [10]
            c = [0.1]

        charging_power = res[0]
        price = c[0]

        if charging_power == 0:
            # Case: Do not bid.
            self.bid = None
            self.offer = None
            self.trading_state = None
        elif charging_power > 0:
            # Case: Bid on energy.
            self.bid = [[price, charging_power, self.id]]
            self.offer = None
            self.trading_state = "buying"
        else:
            # Case: Sell energy.
            self.bid = None
            self.offer = [[price, charging_power, self.id]]
            self.trading_state = "supplying"

    def announce_bid(self):
        # If the electrolyzer is bidding on electricity, the bid is added to the bidding list.
        battery_log.info('Battery bidding state is {}'.format(self.trading_state))

        if self.trading_state == 'buying':
            self.model.auction.bid_list.append(self.bid)
        elif self.trading_state == "supplying":
            self.model.auction.offer_list.append(self.offer)

    def update_state(self, charging_energy, temperature=273.15+10):
        """
        Update the states of the battery (state of charge and max. capacity, which decreases due to aging).

        :param charging_energy: The amount of electricity received (pos) or distributed (neg) [kWh].
        :param temperature: The battery temperature [K]
        """
        self.temperature.append(temperature)
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
            # Calculate the relative throughput.
            throughput = -charging_energy / self.discharge_eff / self.capacity_init
        elif charging_energy > 0:
            # Case: Charging the battery. Calculate the new stored electricity [kWh].
            self.stored_electricity += charging_energy * self.charge_eff
            # Calculate the relative throughput.
            throughput = charging_energy * self.charge_eff / self.capacity_init
        else:
            throughput = 0
        # calculate total charge throughput Q
        self.total_charge_throughput += self.cell_capacity_init * throughput
        # Update the capacity due to aging [kWh].
        capacity_loss_rel = self.get_capacity_loss_by_aging()
        self.capacity = (1 - capacity_loss_rel) * self.capacity_init

        if self.stored_electricity > self.capacity:
            # To prevent rounding errors set amounts of stored electricity above max to the max.
            self.stored_electricity = self.capacity
        elif abs(self.stored_electricity) < 10**-5:
            # To prevent rounding errors set very very small amounts of stored energy to zero.
            self.stored_electricity = 0

        # Update the time the battery was used [d].
        self.time_in_use += self.interval_time / 60 / 24
        battery_log.info("Battery states updated. Capacity loss due to aging is {} kWh.".format(capacity_loss_rel))

    def get_charging_limit(self):
        # Calculates how much energy can max. be bought or distributed in the next time step.
        # Output: array [max. bought, max. distributed] in kWh.

        # Calculate the two limits for discharging: 1. stored energy, 2. C-rate limit [kWh].
        max_discharge_stored = self.stored_electricity * self.discharge_eff
        max_discharge_c_rate = self.capacity_init * self.c_rate * self.interval_time / 60 * self.discharge_eff
        # Max. amount of energy that can be distributed for the next step [kWh].
        max_distributed = min(max_discharge_stored, max_discharge_c_rate)

        max_charge_stored = (self.capacity - self.stored_electricity) / self.charge_eff
        max_charge_c_rate = self.capacity_init * self.c_rate * self.interval_time / 60 / self.charge_eff
        max_bought = min(max_charge_stored, max_charge_c_rate)

        return [max_bought, max_distributed]

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


if __name__ == "__main__":
    model_dummy = []
    unique_id = 1
    battery = Battery(unique_id, model_dummy)
    charge_rate = 2
    temp_cycle = list(range(273+10, 273+60, 10))
    for i_step in range(96*365):
        this_temp = 273+20
        battery.update_state(charge_rate, this_temp)
        if battery.capacity == battery.stored_electricity or battery.stored_electricity == 0:
            # If the battery is full or empty, change from charging to discharging or vice versa.
            charge_rate *= -1

        if i_step % 100 == 0:
            print("Step {}: Battery states updated. Stored energy {:2} kWh, Capacity of battery is {:.5} kWh. This temp: {}".format(
                i_step, battery.stored_electricity, battery.capacity, this_temp))

