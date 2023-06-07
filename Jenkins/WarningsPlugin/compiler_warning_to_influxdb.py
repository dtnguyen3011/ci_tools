"""
    Description: script to get info from generated warning file __Warning.txt and push warning data to influxdb
    Version: 3.7
    Library: influxdb
    Ex: python compiler_warning_to_influxdb.py -i ./__Warning.txt -ht abtv55170.de.bosch.com -pt 8086 -db ccda_radar -m test
"""
import re
from collections import Counter
from influxdb import InfluxDBClient
from datetime import datetime
import argparse


def parse_args():
    description = "Get compiler warning data from generated warning file to influxdb"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input-file', required=True,
                        help='Input warning txt file')
    parser.add_argument('-bn', '--build-number',
                        help='Jenkins build number')
    parser.add_argument('-ht', '--host', default='abtv55170.de.bosch.com',
                        help='Influxdb host')
    parser.add_argument('-pt', '--port', default=8086,
                        help='Influxdb port')
    parser.add_argument('-db', '--database', default='ccda_radar',
                        help='Database name in Influxdb')
    parser.add_argument('-m', '--measurement',
                        help='Measurement name in Influxdb')
    return parser.parse_args()

def get_data_from_warning_log(warning_file):
    raw_data = []
    data = []
    with open(warning_file, "r") as f:
        lines = f.read().splitlines()
    lines = list(filter(None, lines))

    for i in lines:
        try:
            found = re.search('warning\s#\d+-\w', i).group(0)
            raw_data.append(found.replace(' ', ''))
        except:
            continue
    temp = dict(Counter(raw_data))
    for key, value in temp.items():
        data.append({'name': key, 'Occurents': value})
    print(data)
    return data

def push_to_influxdb(args, time_stamp, data):
    for i in data:
        if args.build_number:
            influx_data = f'{args.measurement},type={i["name"]},build={args.build_number} Occurents={i["Occurents"]} {time_stamp}'
        else:
            influx_data = f'{args.measurement},type={i["name"]} Occurents={i["Occurents"]} {time_stamp}'
        print(f"Data: {influx_data}")
        client.write_points(influx_data, database=args.database, time_precision='s', protocol='line')

if __name__ == "__main__":
    args = parse_args()
    data = get_data_from_warning_log(args.input_file)
    if args.measurement:
        client = InfluxDBClient(host=args.host, port=args.port, database=args.database)
        time_stamp = int(datetime.timestamp(datetime.now()))
        push_to_influxdb(args, time_stamp, data)
    else:
        print("Not pushing data to influxdb due to measurement argument was not provided")
