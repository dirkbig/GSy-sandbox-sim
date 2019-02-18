

def peak_shaving_strategy(self):

    # TODO: we want to use this Community Battery to be peak-shaving
    # i.e. a battery that wants to minimize the grid dependency of the local
    # energy market to the DSO grid. Battery needs a forecast of energy import/demand from grid
    # and a forecast of peak to average ratio. Then it can adjust it's local supply such that it floods
    # the market with local supply as soon as the peak-to-average ratio seems to become positive.
    """
    Battery strategy: checks market on local level by aggregating the supply/demand curves of its area;
    it needs to know what extra energy needs to be supplied locally in order to avoid congestion.
    does not need forecasting. ONly needs to forecast when requiring the CESS to work with a limited energy budget
    and thus has to make decisions how to spend it most efficiently.

    >> is this level of market transparency realistic?? Bids /offers might exist on blockchain, might be anonymised through
    a smart-contract

    """
    self.model.auction.bi

