
from source.electrolyzer import Electrolyzer
from source.data import Data
import source.const as const


class DepthVar:
    """ Class that allows to create a sub-class structure (e.g. a.b.c = d) """
    def add_method(self, method_name, val=None):
        if val is None:
            val = DepthVar()

        return self.__setattr__(method_name, val)


def run():
    # While the creation of the electrolyzer instance requires a model instance, it has to be created
    ts_data = Data()

    model = DepthVar()
    model.add_method("data")
    model.data.add_method("electrolyzer_list", ts_data.electrolyzer_list)
    model.data.add_method("utility_pricing_profile", ts_data.utility_pricing_profile)

    ely = Electrolyzer(1, model)
    # Set warning filter so that a warning that appears multiple times is not suppressed.
    # warnings.simplefilter('always', UserWarning)

    for i_timestep in range(2000):
        # Define the power bought for the electrolyzer [kW].
        ely_power = 250
        ely.model.step_count = i_timestep

        ely.pre_auction_round()

        print("Time step {:3.0f}; Time passed {:5.0f} min; Ely power {:.2f} kW; Voltage {:.2f} V; Ely cur. {:.2f}"
              " A; Cur. density {:.4f} A/cm²; Stored mass {:6.2f} kg; Demand {:4.2f} kg; Demand not met {:4.2f} kg, "
              "Temp: {:.2f}".format(i_timestep, i_timestep*const.market_interval, ely.power, ely.voltage, ely.current,
                ely.cur_dens, ely.stored_hydrogen, ely.track_demand[-1], ely.demand_not_fulfilled, ely.temp))

    print("\nTest finished.")






