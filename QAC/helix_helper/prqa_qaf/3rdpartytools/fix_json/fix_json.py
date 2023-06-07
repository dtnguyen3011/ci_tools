import os
import subprocess
import sys
import fnmatch
import shutil
import json
import re
import argparse
import time
import csv

def argumentparser():
    parser = argparse.ArgumentParser(
        description='Fix for compile_commands.json that contain @<<',
        usage='python fix_json.py -in / --input [compile_commands.json]\n',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('-in', '--input',
        help='Path to compile_commands.json',
        required=True
    )

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    print("---")
    print("# fix_json python")
    fix_json_script_path = os.path.dirname(os.path.realpath(__file__))        
    print("# fix_json_script_path: " + str(fix_json_script_path))
    
    args = argumentparser()
    print("# in: " + str(args.input))

    modified_buildlog = args.input + ".fixed.json"

    modified_json = []
    with open(args.input, "rt") as fin:
        data = json.load(fin, strict=False)
        print("Original JSON length: " + str(len(data)))
        for item in data:
            
            
            fixed_command = item['command'].replace('@<<', '').replace('<<', '').replace('\n', '').replace('\r', '')
            # print(fixed_command)

            fixed_item = {
                    "directory": item['directory'],
                    "command": fixed_command,
                    "file": item['file']
                }

            modified_json.append(fixed_item)

    print("Fixed JSON length: " + str(len(modified_json)))
    with open(modified_buildlog, "wt") as fout:
        json.dump(modified_json, fout, sort_keys = True, indent = 4,
               ensure_ascii = False)

    print("- done -")