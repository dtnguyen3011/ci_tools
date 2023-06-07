from influxdb import InfluxDBClient
import re
import argparse
from datetime import datetime
from influxdb import InfluxDBClient


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', dest='inputfile', required=True,
                        help='Input Memory Check file need to be put as an argument. It should be the output of mem_level_analysis.pl')
    parser.add_argument('-bn', '--build-number',
                        help='Jenkins build number')
    parser.add_argument('-ht', '--host', default='abtv55170.de.bosch.com',
                        help='Influxdb host')
    parser.add_argument('-pt', '--port', default=8086,
                        help='Influxdb port')
    parser.add_argument('-dv', '--device', dest='device', required=False,
                        default="Ukn_Device")
    parser.add_argument('-db', '--database', default='ccda_radar',
                        help='Database name in Influxdb')
    parser.add_argument('-m', '--measurement', required=True,
                        help='Measurement name in Influxdb')
    return parser.parse_args()


class Section_element:
    def __init__(self,Name,Free,Free_percentage,Used,Used_percentage):
        self.Name = Name
        self.Free = int (Free)
        self.Used = int (Used)
        self.Free_percentage = float(Free_percentage)
        self.Used_percentage = float(Used_percentage)
        self.Total = Free + Used
    def Calc_Used_percent(self,Sum_Used):
        return (int(round((self.Used/Sum_Used *10000))))/100.00

def get_data(input_file):
    #Process Input file
    with open(input_file, "r") as input_file:
        input_str = input_file.read()
        # Check if input file is empty
        if not input_str.strip():
            raise ValueError ("[ERROR] Input file is empty")

    print ("-------------------------")
    print ("-----RAM/ROM report:-----")
    print ("-------------------------")
    print ("")
    print (input_str)
    #Catching memory section. 
    # e.g: 0 DSPR	17542	7.1%	228186	92.9% 
    #   OR PFLS 0	-324114	-19.7%	1962514	119.8%
    get_Section_regex = re.compile(r'(^\w+.*)\t(\-*\d*)\t(\d*.*\%)\t(\d*)\t(\d*.*\%)',re.MULTILINE)
    matches = get_Section_regex.findall(input_str)

    #Collect all the memory session
    Sections = []    
    try:
        for match in matches:
            #Remove all non character in string, except " ","-" and "_"
            match_str_0 = re.sub("[^A-Za-z0-9. _-]+","",str(match[0]))
            match_str_1 = re.sub("[^A-Za-z0-9. _-]+","",str(match[1]))
            match_str_2 = re.sub("[^A-Za-z0-9. _-]+","",str(match[2]))
            match_str_3 = re.sub("[^A-Za-z0-9. _-]+","",str(match[3]))
            match_str_4 = re.sub("[^A-Za-z0-9. _-]+","",str(match[4]))
            Sections.append(Section_element(match_str_0,int(match_str_1),float(match_str_2),int(match_str_3),float(match_str_4)))

        Index_Of_RAM_Sec = next((i for i, x in enumerate(Sections) if x.Name == "SUM RAM"), -1)        
        Index_Of_ROM_Sec = next((i for i, x in enumerate(Sections) if x.Name == "SUM ROM"), -1)
    except IndexError:
        # Handle Index error in case could not found any matching
        Index_Of_RAM_Sec = -1
    
    if (Index_Of_RAM_Sec == -1) or (Index_Of_ROM_Sec == -1) or (Index_Of_ROM_Sec == Index_Of_RAM_Sec+1) or (Index_Of_RAM_Sec == Index_Of_ROM_Sec+1):
        #throw error here
        raise ValueError ("Memory Report lacks of information")

    #Check if RAM Section is before ROM Section or not, set offset for index
    if Index_Of_RAM_Sec < Index_Of_ROM_Sec:
        RAM_Section_Offset = 0
        ROM_Section_Offset = Index_Of_RAM_Sec + 1
        Number_RAM_Section = Index_Of_RAM_Sec
        Number_ROM_Section = Index_Of_ROM_Sec - Index_Of_RAM_Sec - 1
    else:
        RAM_Section_Offset = Index_Of_ROM_Sec + 1
        ROM_Section_Offset = 0
        Number_RAM_Section = Index_Of_RAM_Sec - Index_Of_ROM_Sec - 1 
        Number_ROM_Section = Index_Of_ROM_Sec

    data = []

    # Data for RAM
    RAM_Section_Name = []
    RAM_Used = []
    RAM_Free = []
    RAM_Total = []
    RAM_Used_Percent = []
    RAM_Free_Percent = []


    # Raw Value calculation
    for i in range (Number_RAM_Section):
        #Bar Chart
        RAM_Used.append(Sections[i+RAM_Section_Offset].Used/1024)
        RAM_Free.append(Sections[i+RAM_Section_Offset].Free/1024)
        RAM_Total.append(Sections[i+RAM_Section_Offset].Total/1024)
        RAM_Used_Percent.append(Sections[i+RAM_Section_Offset].Used_percentage)
        RAM_Free_Percent.append(Sections[i+RAM_Section_Offset].Free_percentage)
        RAM_Section_Name.append(Sections[i+RAM_Section_Offset].Name)
        data.append({'Type': 'RAM', 'Section': RAM_Section_Name[i], 'FreeKB': RAM_Free[i], 'UsedKB': RAM_Used[i], \
        'FreePer': RAM_Free_Percent[i], 'UsedPer': RAM_Used_Percent[i], 'TotalKB': RAM_Total[i]})

    # Data for ROM
    ROM_Section_Name = []
    ROM_Used = []
    ROM_Free = []
    ROM_Total = []
    ROM_Used_Percent = []
    ROM_Free_Percent = []

    # Raw Value calculation
    for i in range (Number_ROM_Section):
        #Bar Chart
        ROM_Used.append(Sections[i+ROM_Section_Offset].Used/1024)
        ROM_Free.append(Sections[i+ROM_Section_Offset].Free/1024)
        ROM_Used_Percent.append(Sections[i+ROM_Section_Offset].Used_percentage)
        ROM_Free_Percent.append(Sections[i+ROM_Section_Offset].Free_percentage)
        ROM_Total.append(Sections[i+ROM_Section_Offset].Total/1024)
        ROM_Section_Name.append(Sections[i+ROM_Section_Offset].Name)
        data.append({'Type': 'ROM', 'Section': ROM_Section_Name[i], 'FreeKB': ROM_Free[i], 'UsedKB': ROM_Used[i], \
        'FreePer': ROM_Free_Percent[i], 'UsedPer': ROM_Used_Percent[i], 'TotalKB': ROM_Total[i]})
    return data

def post_to_influxdb(data, mea, device, client, time_stamp, build_number=0):
    for i in data:
        json_body = [
            {
                "measurement": mea,
                "tags": {
                    "device": device,
                    "Section": i["Section"],
                    "Type": i["Type"],
                    "Build": build_number
                },
                "time": time_stamp,
                "fields": {
                    "FreeKB": i["FreeKB"],
                    "UsedKB": i["UsedKB"],
                    "FreePer": i["FreePer"],
                    "UsedPer": i["UsedPer"],
                    "TotalKB": i["TotalKB"]
                }
            }
        ]
        print(json_body)
        client.write_points(json_body)


if __name__ == '__main__':
    args = parse_args()
    time_stamp = datetime.now()
    client = InfluxDBClient(host=args.host, port=args.port, database=args.database)
    influxdb_data = get_data(args.inputfile)
    post_to_influxdb(influxdb_data, args.measurement, args.device, client, time_stamp, args.build_number)
