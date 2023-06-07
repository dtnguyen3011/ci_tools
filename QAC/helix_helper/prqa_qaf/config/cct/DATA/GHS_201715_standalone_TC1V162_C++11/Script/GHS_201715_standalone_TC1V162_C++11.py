import os, inspect
import sys
import platform

# GHS Multi compiler system include
def sysInclude():
	try:
		current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
		scriptFile = inspect.getfile(inspect.currentframe())
		fileName = os.path.basename(scriptFile)
		cipFilename = os.path.splitext(fileName.strip())[0] + '.cip'
		normal_parent = os.path.dirname(current_dir)
		dataDir = os.path.dirname(normal_parent)
		cctDir = os.path.dirname(dataDir)
		configDir = os.path.dirname(cctDir)
		cipDir = os.path.join(configDir, "cip")
		cipFilepath = os.path.join(cipDir, cipFilename)
		stubDir = os.path.join(normal_parent, "Stub")
		cipFile = open(cipFilepath, 'w')
		
		
        ###############################################################
        ###############################################################
		## Installation Path for GHS
		compInstall = os.path.join('c:',os.sep,'toolbase', 'greenhills_ifx','comp_201715_1fp')
        ###############################################################
        ###############################################################

        	# Stub Directory   
		stubList = [os.path.join(d, t) for d, ds, fs in os.walk(stubDir) for t in ds]
		for dirName in stubList:
			cipFile.write('-i "' + dirName + '"\n')
			cipFile.write('-q "' + dirName + '"\n')
		for fiDir in stubList:
			if fiDir.endswith("prlforceinclude"):
				fileList = [os.path.join(fiDir, x) for x in os.listdir(fiDir)]
				for fn in fileList:
					cipFile.write('-fi "' + fn + '"\n')


		# Compiler include directory
		compInclude = os.path.join(compInstall, "include")
		cipFile.write('-i "' + compInclude + '"\n')
		cipFile.write('-q "' + compInclude + '"\n')
		incList = [os.path.join(d, t) for d, ds, fs in os.walk(compInclude) for t in ds]
		for dirName in incList:
			cipFile.write('-i "' + dirName + '"\n')
			cipFile.write('-q "' + dirName + '"\n')

		# ansi include directory
		ansiInclude = os.path.join(compInstall, "ansi")
		cipFile.write('-i "' + ansiInclude + '"\n')
		cipFile.write('-q "' + ansiInclude + '"\n')
            
        # scxx include directory
		scxxInclude = os.path.join(compInstall, "scxx")
		cipFile.write('-i "' + scxxInclude + '"\n')
		cipFile.write('-q "' + scxxInclude + '"\n')

		cipFile.close()
        			
	except IOError: pass 

if __name__=="__main__":
	if sys.platform == 'win32' :
		sysInclude()

