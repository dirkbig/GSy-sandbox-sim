"""
This script loads the result csv of the last run from ../test_result.csv and gives back a list of lists with all bids.
"""

import csv


def get_result():
    output_array = []
    with open('../test_result.csv') as file:
        filereader = csv.reader(file, delimiter=',')
        for this_row in filereader:
            output_row = []
            if len(this_row) > 1:
                # Case: A trade was made (thus this row does not only consist of the string "No trade was made").
                for i in range(int(len(this_row)/4)):
                    # Slice the string of bids up to bids (each containing of 4 entries).
                    # [id_seller, id_buyer, quantity, price*quantity]
                    row_to_append = this_row[i*4:(i+1)*4]
                    # Set quantity and price*quantity from string (as it is loaded) to float.
                    row_to_append[2] = float(row_to_append[2])
                    row_to_append[3] = float(row_to_append[3])
                    output_row.append(row_to_append)

            output_array.append(output_row)

    return output_array


if __name__ == '__main__':
    res = get_result()
    print(res)

