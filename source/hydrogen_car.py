from mesa import Agent


class HydrogenCar(Agent):
    """ HydrogenCar agent is created through this class """

    """ 
        Electrolyzer produces hydrogen gas. This gas can either be sold 
            - to fueling HydrogenCar objects 
            - or used by a FuelCell object to produce electricity, to be sold on the energy market ]
        This class models the HydrogenCar 
    """
    def __init__(self, _unique_id, model):
        """ Electrolyzer gas station supply (consumption of hydrogen cars) profile can live here """
        pass

    def track_data(self):
        pass