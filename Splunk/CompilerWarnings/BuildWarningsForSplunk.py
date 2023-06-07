import argparse
import os.path
from os import path
import csv
from copy import copy

OutPutFileName = "compiler_warnings.csv"
MetricsList = []

class CBuild_Warning:
    file_path = ""
    file_name = ""
    line = ""
    team = ""
    msg = ""
    type = ""

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-sp', '--source_path', required=True, type=str, help='path where BTC Log File should be generated')
    parser.add_argument('-fn', '--folder_name', required=True, type=str, help='all files from this folder will be analyzed.')
    parser.add_argument('-dp', '--domain_path', required=True, type=str, help='path where the domain.csv is stored')
    parser.add_argument('-mn', '--metric_name', required=True, type=str, help='metric name, csv')

    return parser.parse_args()

def process_of_warnings(module , domain_dic, log_path, ignore_list_path):
# read ignore list file
    ignore_list = []
    with open(ignore_list_path) as file:
        reader = file.readlines()
        for line in reader:
            if line.find('/') != -1:
                ignore_list.append(line.replace('*','').rstrip())
    with open(log_path) as file:
        reader = file.readlines()
    metric = CBuild_Warning()
    for line in reader:
        if line.startswith("WARNING -"):
            print(line)
            items = line.split("\"")
            if len(items) < 2:
                print("Attention: Line has only one element:", line)
                continue
            metric.file_path = items[1]
            items = line.split("/")
            metric.file_name = items[len(items)-1].rstrip("\n")
            continue
        if line.startswith("\t") and line.find("warning #") != -1:
# check ignore liste
            ignore_element_exists = False
            for elem in ignore_list:
                if metric.file_path.find(elem) != -1:
                    print("\tIgnore Path = ", metric.file_path)
                    ignore_element_exists = True
                    break
            if ignore_element_exists == True:
                continue

            items = line.rstrip("\n").split(":")
            metric.line = items[0].replace("\t", "")
            metric.type = items[1]
            metric.msg = items[2] 
# team assignment
            metric.team = "no team"           
            for key in domain_dic:
                values = (domain_dic.get(key))
                if any(metric.file_path.find(mem.replace("\\", "/")) != -1 for mem in values) and metric.file_path.find(module.replace("\\", "/")) != -1:
                    metric.team = key
                    break 
            if metric.file_path.find(module.replace("\\", "/")) != -1 :
                MetricsList.append(copy(metric))



if __name__ == '__main__':
    try:
        ignore_list_path = ""
        args = parse_args()
# check the paths
        if(path.exists(args.domain_path) == False):
            print("Path is not exists:{0}".format(args.domain_path))
            exit(0)
        ignore_list_path = os.path.join(os.path.dirname(args.domain_path), ".gitignore")
        if(path.exists(ignore_list_path) == False):
            print("Path is not exists:{0}".format(ignore_list_path))
            exit(0)
# read domain csv table
        domain_dic = {}
        with open(args.domain_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')# read qac report
            next(csv_reader, None) 
            data = list(csv_reader)
            domin_name = 'default'
            for line in data:
                if line[0] == '' and line[1] != '':
                    domin_name = line[1]
                if line [0] != '':
                    domain_dic.setdefault(domin_name, []).append(line[0]) 

#            for key, value in domain_dic.items() :
#                print (key, value)                
# search and read BTC_Logfile with build warnings
        files = []
        warning_keyword = "BTC_Radar_warninglog"
        abs_path = os.path.abspath(args.source_path)
        print("source_path=", abs_path)
        for r, d, f in os.walk(abs_path):
            for file in f:
                if file.startswith(warning_keyword):
                    files.append(os.path.join(r, file))
                    print("this file was found: ", os.path.join(r, file))
                    process_of_warnings(args.folder_name, domain_dic, os.path.join(r, file), ignore_list_path)
        
        print("----------------------------------------------------")

        file = open(args.metric_name, 'w', newline='')
        with file:
            columns = ['File path', 'File name', 'Row', 'Column', 'Components', 'Team', 'Message', 'Severity', 'Type', 'Number of occurrences']
            writer = csv.DictWriter(file, fieldnames=columns)    

            writer.writeheader()
            for metric in MetricsList:
                  writer.writerow({'File path' : metric.file_path, 'File name': metric.file_name, 'Row': metric.line, 'Column': '0', 'Components': '0', 'Team': metric.team, 'Components': metric.msg, 'Severity': '0', 'Type': metric.type, 'Number of occurrences': '0'})

    except NameError:
        print("Error")
        print("arguments:{0}".format)