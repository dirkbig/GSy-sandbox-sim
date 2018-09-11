# Pay as Clear Market 

agent-based model using MESA package modeling a two-sided market, pay-as-clear pricing rule based micro-grid energy market. Goal is to simulate a grid with households using plug-and-play bidding strategies and devices according a predefined grid set-up

## Getting started

This is a project in Python 3.6.3. We advice to use a virtual environment.

Install dependencies (MESA, matlibplot, seaborn, and some standard ones), by directing pip-installer towards the requirements.txt

```
pip install -r requirements.txt
```

## Run simulation

run the micro-grid simulator file in the command-line
```
python run_microgrid.py
```

## Results

A plot is automatically generated and opened, showing all bids and offers in a aggregated demand/supply curve, with an market clearing quantity. For pay-as-clear, this corresponds directly with the clearing price on the Y-axis.

## Contribution
This is a research collaboration between Grid Singularity / Energy Web Foundation - Reiner Lemoine Institut

* **Dirk van den Biggelaar**
* **Fatuma Mohammed Ali**
* **Marlon Fleck**
* **Jorn Hartmann**

