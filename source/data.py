import numpy as np
from source import const


class Data(object):
    def __init__(self):
        """initialise data sets"""

        _num_households = 100

        # self.load_profile =             [8, 5, 7, 5, 4, 3, 3, 2, 2, 1, 1, 4, 3, 2, 1, 0]
        # self.storage_profile =          [0, 0, 0, 1, 1, 9, 2, 2, 1, 2, 4, 2, 2, 1, 4, 1]
        # self.production_profile =       [1, 0, 0, 9, 0, 4, 2, 4, 2, 6, 9, 2, 5, 3, 2, 5]
        # self.capacity =                 [5, 5, 5, 5, 5, 1, 5, 2, 1, 4, 5, 2, 2, 2, 2, 2]

        self.load_profile = 1.8*np.random.rand(_num_households)
        self.storage_profile = np.random.rand(_num_households)
        self.production_profile = np.random.rand(_num_households)
        self.capacity = np.random.rand(_num_households)

        assert len(self.load_profile) == len(self.storage_profile) == len(self.production_profile) == len(self.capacity)
        self.N = min(const.max_households + 1, len(self.load_profile))

        # TODO: add time series data from Stanford SMART* data-set
