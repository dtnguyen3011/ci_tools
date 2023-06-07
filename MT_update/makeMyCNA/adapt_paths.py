#!/usr/bin/python
#Script: adapt_paths.py
#Desp: adapt the paths in makeMyCNA_local.ini before running makeMyCNA_Jenkins.bat
#Ver: 1.0
#Autor: zhy2lr
#Last update by :hpm81hc
#Copyright: Robert Bosch GmbH, 2019

import sys, getopt
import os, time

# https://gist.github.com/vladignatyev/06860ec2040cb497f0f3
def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def main(argv):

	flag_canape = 0
	flag_temp = 0
	flag_list = 0
	flag_prjname = 0
	
	try:
		opts, args = getopt.getopt(argv,"hm:s:e:c:t:l:p:",["mt=", "scom=", "elf=", "canape=", "temp=", "list=", "prjname="])
	except getopt.GetoptError:
		print('[ERROR]')
		print('Wrong input given!')
		print('At least both paths to measurement and scom_gen folders must be specified!')
		print('usage: $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> -e <path to elf>')
		print('       $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> --canape <path to CANAPE> --temp <path to temp folder> --list <path to customer list> --prjname <project name>')
		sys.exit(2)
	if len(opts)<1:
		print('[ERROR]')
		print('I need at least 3 arguments with options!')
		print('usage: $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> -e <path to elf>')
		print('       $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> --canape <path to CANAPE> --temp <path to temp folder --list <path to customer list> --prjname <project name>')
		sys.exit(2)
	elif len(opts)==1:
		if opts[0][0] == '-h':
			print('[INFO]')
			print('------------------------------------------------------------- help -----------------------------------------------------------------')
			print('usage: $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> -e <path to elf>')
			print('       $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> --canape <path to CANAPE> --temp <path to temp folder> --list <path to customer list> --prjname <project name>')
			print('       The paths to RadarFC.cna and the path to scom_gen are mandatory. The paths to CANAPE and the path to temp folder are optional')
			print('       !The sequence of the arguments matters! You can skip --canape and only give --temp, but you can\'t switch their positions!')
			print('       !If your path contains space, you have to quote it!')
			print('       The default path to CANAPE:   C:\Program Files\Vector CANape 18.0\Exec64\CANape64.exe')
			print('       The default temp folder:      C:\\tempMT')
			print('       For more information please contact Pham Ngoc Thai (RBVH/EDA15)!')
			sys.exit()
		else:
			print('[ERROR]')
			print('At least both paths to measurement and scom_gen folders must be specified!')
			print('usage: $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> -e <path to elf>')
			print('       $ adapt_paths.py -m <path to RadarFC.cna> -s <path to scom_gen> --canape <path to CANAPE> --temp <path to temp folder> --list <path to customer list> --prjname <project name>')
			sys.exit(2)
	for opt, arg in opts:
		if opt in ("-m", "--mt"):
			path_mt = arg
		elif opt in ("-s", "--scom"):
			path_scom = arg
		elif opt in ("-e", "--elf"):
			path_elf = arg
		elif opt in ("-c", "--canape"):
			path_canape = arg
			flag_canape = 1
		elif opt in ("-t", "--temp"):
			path_temp = arg
			flag_temp = 1
		elif opt in ("-l", "--list"):
			path_list = arg
			flag_list = 1
		elif opt in ("-p", "--prjname"):
			project_name = arg
			flag_prjname = 1

	print('-----------------------------------------------------')
	print('Generating makeMyCNA_local_cust.ini !!!')
	print('please wait...')
	print('')

	with open('makeMyCNA_local.ini','r') as initfile:
		lines = initfile.readlines()
	for i, line in enumerate(lines):
		if ("[TEMP_PATH]" in line) and (flag_temp==1):
			print('temp folder path will be adapted to '+path_temp)
			lines[i+1] = "Path = "+path_temp+"\n"
		if ("[CANAPE]" in line) and (flag_canape==1):
			print('CANAPE path will be adapted to '+path_canape)
			lines[i+2] = "Path = "+path_canape+"\n"
		if "[CNA]" in line:
			print('MT path will be adapted to '+path_mt )
			lines[i+1] = "Path = "+path_mt+"\n"
		if "Scom_gen_path" in line:
			print('scom_gen path will be adapted to '+path_scom)
			lines[i] = "Scom_gen_path = "+path_scom+"\n"
		if ("Custom_list_path_0" in line) and (flag_list==1):
			print('customer list path will be adapted to '+path_list)
			lines[i] = "Custom_list_path_0 = "+path_list+"\n"
		if "ELF_path" in line:
			print('ELF_path will be adapted to '+path_elf)
			lines[i] = "ELF_path = "+path_elf+"\n"
		if ("[PROJECT]" in line) and (flag_prjname==1):
			print('Project name will be adapted to '+project_name)
			lines[i+1] = "Name = "+project_name+"\n"

	with open('makeMyCNA_local_cust.ini','w+') as output:
		output.writelines(lines)
    
	# just to have some fun at work ;-)
	total = 100
	i = 0
	while i <= total:
		status = 'Processing'
		if i == total:
			status = 'DONE!!!!!'
		progress(i, total, status=status)
		time.sleep(0.01)
		i += 1

if __name__ == "__main__":
    main(sys.argv[1:])
