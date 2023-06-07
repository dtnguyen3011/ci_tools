"""
    Description: get source code statistics(language, code, comment, blankline) from cloc.xml which get created from cloc tool, and push data to influxdb.
    Version: 3.7
    Library: influxdb, panda
    Ex: python get_sloc_data.py -i cloc.xml -ht abtv55170.de.bosch.com -pt 8086 -db ccda_radar -m test
"""
import xml.etree.ElementTree as ET
import argparse
from influxdb import InfluxDBClient
from datetime import datetime
import pandas as pd 

def parse_args():
    description = "Get SLOC data from xml and push to influxdb"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input-file', required=True,
                        help='Input cloc.xml file')
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

def get_data_from_xml(xml_file):
    raw_data = []
    data  = []
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Find elements with tag 'file' in xml
    for test in root.iter('file'):
        raw_data.append(test.attrib)

    # Convert value from string to int and remove whitespace from language value
    for i in raw_data:
        del i['name']
        i['code'] = int(i['code'])
        i['blank'] = int(i['blank'])
        i['comment'] = int(i['comment'])
        i['language'] = i['language'].replace(" ", "")

    # Aggregate blank lines, code and comment for each kind of languages
    df = pd.DataFrame(raw_data)
    grouped = df.groupby(['language']).agg(sum)
    data = grouped.reset_index().to_dict('records')
    return data

def push_to_influxdb(args, time_stamp, data):
    for i in data:
        if args.build_number:
            influx_data = f'{args.measurement},language={i["language"]},build={args.build_number} comment={i["comment"]},code={i["code"]},blank={i["blank"]} {time_stamp}'
        else:
            influx_data = f'{args.measurement},language={i["language"]} comment={i["comment"]},code={i["code"]},blank={i["blank"]} {time_stamp}'
        print(f"Data: {influx_data}")
        client.write_points(influx_data, database=args.database, time_precision='s', protocol='line')


if __name__ == "__main__":
    args = parse_args()
    data = get_data_from_xml(args.input_file)
    if args.measurement:
        client = InfluxDBClient(host=args.host, port=args.port, database=args.database)
        time_stamp = int(datetime.timestamp(datetime.now()))
        push_to_influxdb(args, time_stamp, data)
    else:
        print("Not pushing data to influxdb due to measurement argument was not provided")
