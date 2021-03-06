# Local Energy Market Model

Agent-based model using MESA package modeling a two-sided market, pay-as-clear pricing rule based micro-grid energy market. Goal is to simulate a grid with households using plug-and-play bidding strategies and devices according a predefined grid set-up. Includes
3 pricing algorithms; Pay as Bid (i.e. discriminatory auction), Pay as Clear (i.e. uniform auction) and the McAfee Auction.

## Getting started

This is a project in Python 3.6.3. We advice to use a virtual environment.

Clone repo into a dedicated folder (in your home directory). In terminal, located inside this folder, do:

```
git clone https://github.com/dirkbig/pac
```

Install dependencies (MESA, matlibplot, seaborn, and some standard ones), by directing pip-installer towards the requirements.txt

```
pip install -r requirements.txt
```

## Run simulation

Run the micro-grid simulator file in the command-line
```
python run_microgrid.py
```

Since dependency on Matlibplot, the 'python is not installed as framework' error could be occurring. If so:
```
echo "backend: TkAgg" >> ~/.matplotlib/matplotlibrc
python run_microgrid.py
```

## Results

A plot is automatically generated and opened, showing all bids and offers in a aggregated demand/supply curve, with an market clearing quantity. For pay-as-clear, this corresponds directly with the clearing price on the Y-axis. Not adviced when running
large amounts of steps.

When running data,py as main, agent profiles are plotted, according to the grid_config.py file. grid_config.py is used by microgrid simulation.

## Contribution
This is a research collaboration between Grid Singularity / Energy Web Foundation - Reiner Lemoine Institut

* **Dirk van den Biggelaar** - GSy
* **Fatuma Mohammed Ali** - GSy
* **Marlon Fleck** - RLI
* **Jorn Hartmann** - RLI

