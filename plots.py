import matplotlib.pyplot as plt


def clearing_snapshot(clearing_quantity, clearing_price, sorted_x_y_y_pairs_list):
    # TODO: export these demand/supply curves
    x_quantities = []
    y_bid_prices = []
    y_offer_prices = []

    for i in range(len(sorted_x_y_y_pairs_list)):
        x_quantities.append(sorted_x_y_y_pairs_list[i][0])
        y_bid_prices.append(sorted_x_y_y_pairs_list[i][1])
        y_offer_prices.append(sorted_x_y_y_pairs_list[i][2])

    fig, ax = plt.subplots()

    ax.step(x_quantities, y_bid_prices, label='bids')
    ax.step(x_quantities, y_offer_prices, label='offers')
    if clearing_quantity is not None:
        ax.axvline(x=clearing_quantity, color='black', linestyle='--')
        ax.axhline(y=clearing_price, color='black', linestyle='--')
    ax.legend()
    ax.set(xlabel='quantity', ylabel='price',
           title='clearing markets aggregate demand and supply blocks')
    plt.show()

