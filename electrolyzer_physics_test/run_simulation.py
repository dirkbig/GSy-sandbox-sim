from electrolyzer_physics_test.electrolyzer import Electrolyzer


Ely = Electrolyzer()

for i_second in range(8000):
    ely_voltage = [0, 0, 150, 0]

    Ely.update_power(ely_voltage)

    print("Second {:.0f}; Ely power {:.2f} kW; Ely current {:.2f} A; Temp: {:.2f}".format(
        i_second, Ely.power, Ely.current, Ely.temp))

