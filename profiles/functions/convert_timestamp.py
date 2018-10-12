from datetime import datetime


def unix_to_datestring(unix_timestamp):
    # Convert a UNIX timestamp to a date string in the format "yyyy.MM.dd hh:mm".

    # In case the UNIX timestamp is given as a string, convert it to an integer.
    unix_timestamp = int(unix_timestamp)
    # Return the converted timestamp.
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%d.%m.%Y %H:%M')


def convert_ts_utd(ts_name, ts_converted_name):
    import csv
    # Load a timeseries with the name ts_name with UNIX timestamp, converts it to timeseries with a date string
    # timestamp and saves it with the name ts_converted_name.

    # Load the timeseries from csv file.
    with open(ts_name, newline='') as csvfile:
        ts_reader = csv.reader(csvfile, delimiter=',')
        ts_converted = []
        for row in ts_reader:
            ts_converted.append([unix_to_datestring(row[0]), row[1]])

    # Write the new timeseries to a file.
    with open(ts_converted_name, 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerows(ts_converted)


if __name__ == '__main__':
    # Convert the UNIX timestamps of a timeseries to date strings in the format "yyyy.MM.dd hh:mm".
    ts_load = ''
    ts_save = ''
    convert_ts_utd(ts_load, ts_save)

    print(unix_to_datestring(1301702400))

