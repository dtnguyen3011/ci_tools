'''
    File name: Draw_Graph_Statistics_Branch_Number.py
    Author: Long Phan Hai (RBVH/ESS6)
    Date created: 28/02/2019
    Date last modified: 05/04/2019
    Python Version: 2.7 || 3.5
    Library: matplotlib
'''

import argparse
import re
import json
import os
import sys
import matplotlib.pyplot as pyplot
import matplotlib.dates as mdates
import datetime
import numpy

def parse_args():
    description = "Draw Graph Branch Number Statistics Script"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i', '--input-file', dest='inputfile', required=True,
                        help='json Input file of the  script, should be output of Statistics_Branch_Number.py, which have document structure')   
    parser.add_argument('-o', '--output-path', dest='outputpath', required=False,
                        default=os.path.dirname(os.path.abspath(
                            sys.argv[0])) + os.sep,
                        help='Output path of the json output file,[PATH]/branch_data.html, branch_data.png')                                   
    return parser.parse_args()

class Branch_Statistic_Graph_data:
    def __init__(self,Date,Branch):
        Date = re.split (r'\-',Date)
        self.Date = datetime.datetime(int(Date[0]),int(Date[1]),int(Date[2]),0,0,0)
        self.Branch = Branch

if __name__ == '__main__':
    #Handle arguments
    args = parse_args()
    input_file = args.inputfile
    output_path = args.outputpath
    originalDir = os.getcwd()
    bad_input = False

    #Create Output Folder
    if not os.path.exists(output_path):
        try:
            os.mkdir(output_path)
        except ValueError: #cannot create output directory
            bad_input = True
            
    if bad_input ==True:
        raise ValueError ("Cannot Create Output Directory")

    #Move to output directory
    os.chdir(output_path)

    with open(input_file) as inputfile:
        Data = json.load(inputfile)

    #Process data
    Graph_Data = []
    Data_IDs = []

    #Doing a sort base on "Data_ID" to get sorted document by time and set it to Graph_Data.
    #The Data_ID from MongoDB is unique, so the simple sorting without exception handling can be used.
    Data_IDs = [x["Data_ID"] for x in Data['document'] ]

    #Make Data_ID as unique, to make sure only
    Data_IDs = set(Data_IDs)
    #Convert back to list and sort
    Data_IDs = list(Data_IDs)
    Data_IDs.sort()

    for x in Data_IDs:
        for y in Data['document']:
            if (y['Data_ID'] == x):
                Graph_Data.append(Branch_Statistic_Graph_data(y['Date'],y['Branch']))

    #Draw the graph here
    Row_ind = numpy.arange(len(Graph_Data))
    Date_Data  = [mdates.date2num(x.Date) for x in Graph_Data]
    Branch_Data  = [x.Branch for x in Graph_Data]

    fig, ax = pyplot.subplots()
    
    pyplot.ylabel ('Branch Number over the time')
    pyplot.title ('Branch Statistics')
    Locator = mdates.AutoDateLocator()
    datetimefmt = mdates.AutoDateFormatter(Locator)
    ax.xaxis.set_major_formatter(datetimefmt)
    ax.xaxis.set_major_locator(Locator)
    pyplot.yticks(numpy.arange(0,max(Branch_Data),100))
    p1 = ax.plot(Date_Data,Branch_Data)
    ax.grid(True)
    fig.autofmt_xdate()
    pyplot.savefig('branch_data.png')  

    #Making html Report
    with open("branch_data.html", "w+") as RAM_output:
        RAM_output.write ("<p><img src=\"branch_data.png\" alt=\"\" /></p>")

    #Change back to current directory
    os.chdir(originalDir)