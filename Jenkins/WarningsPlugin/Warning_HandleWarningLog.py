
import re
import sys
import argparse
import os

def parse_args():
    description = "GHS Warning Log handling, filter out not needed Warning and clean redundence Errors/Warnings"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-d', '--folder-list', dest='folderlist', required=False,
                        default="",
                        help='The list of folder that this script shall filter inside Warning Log. Using "," to split folders. E.g: appl,ip_if ')
    parser.add_argument('-i', '--input-file', dest='inputfile', required=True,
                        help='Input Log file need to be put as an argument.')
    parser.add_argument('-o', '--output-file', dest='outputfile', required=True,
                        help='Output Log file need to be put as an argument.')                    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    input_file_name = args.inputfile 
    input_file = open(input_file_name, "r")
    folderlists = list(str(args.folderlist).split(','))
    #check if Output folder parameter has output_folder and folder was created or not
    output_dir , output_file_name = os.path.split(args.outputfile)
    output_dir = str(output_dir)
    if output_dir:
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
    #create output file
    output_file = open(args.outputfile, "w")

    #matching_str = "(?:\.|[A-Z]:)(.*)\,\s*line\s*(\d+):\s*(warning|error)\s*([^:]+):\s*(?m)([^\^]*)\s*\^"
    rx_sequence = re.compile (r"\"(?:\.|[A-Z]:)(.*)\,\s*line\s*(\d+):\s*(warning|error)\s*([^:]+):\s*(?m)([^\^]*)\s*\^",re.MULTILINE)
    matchs = rx_sequence.finditer (input_file.read())
    matchs = set(matchs)
    match_str = ""
    if not folderlists:
        for match in matchs:
            match_str = str(match.group())
            match_str = match_str + "\n"
            match_str = match_str.replace("\", line "," , line ")
            output_file.write(match_str)
    else:
        for folder in folderlists:
            folder_prog = re.compile (folder)        
            for match in matchs:
                match_str = str(match.group())
                match_str = match_str + "\n"
                match_str = match_str.replace("\", line "," , line ")
                match_folder = re.search(folder_prog,match_str)
                if match_folder:
                    output_file.write(match_str)

        

