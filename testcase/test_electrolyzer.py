
from source.Electrolyzer import Electrolyzer
from source.data_methods import csv_read_load_h2
import source.const as const


class DepthVar:
    """ Class that allows to create a sub-class structure (e.g. a.b.c = d) """
    def add_method(self, method_name, val=None):
        if val is None:
            val = DepthVar()

        return self.__setattr__(method_name, val)


def run():
    # While the creation of the electrolyzer instance requires a model instance, it has to be created
    h2_load = csv_read_load_h2()

    model = DepthVar()
    model.add_method("data")
    model.data.add_method("h2_load_list", h2_load)

    ely = Electrolyzer(1, model)
    # Set warning filter so that a warning that appears multiple times is not suppressed.
    # warnings.simplefilter('always', UserWarning)

    for i_timestep in range(2000):
        # Define the power bought for the electrolyzer [kW].
        ely_power = 170
        ely.model.step_count = i_timestep

        ely.update_power(ely_power)
        ely.update_storage()

        print("Time step {:3.0f}; Time passed {:5.0f} min; Ely power {:.2f} kW; Voltage {:.2f} V; Ely cur. {:.2f}"
              " A; Cur. density {:.4f} A/cm²; Stored mass {:6.2f} kg; Demand {:4.2f} kg; Demand not met {:4.2f} kg, "
              "Temp: {:.2f}".format(i_timestep, i_timestep*const.market_interval, ely.power, ely.voltage, ely.current,
                ely.cur_dens, ely.stored_hydrogen, ely.track_demand[-1], ely.demand_not_fulfilled, ely.temp))

    print("\nTest finished.")





