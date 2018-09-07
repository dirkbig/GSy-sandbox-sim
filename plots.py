
import matplotlib.pyplot as plt


def clearing_snapshot(clearing_quantity, clearing_price, x_quantities, y_bid_prices, y_offer_prices):
    # TODO: export these demand/supply curves
    fig, ax = plt.subplots()
    ax = fig.add_subplot(111)
    ax.step(x_quantities, y_bid_prices, label='bids')
    ax.step(x_quantities, y_offer_prices, label='offers')
    if clearing_quantity is not []:
        ax.axvline(x=clearing_quantity, color='black', linestyle='--')
        ax.axhline(y=clearing_price, color='black', linestyle='--')
    ax.legend()
    ax.set(xlabel='quantity', ylabel='price',
           title='clearing markets aggregate demand and supply blocks')
    plt.show()

