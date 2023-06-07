import os, inspect
import dircache
import fnmatch
import dircache

def sysInclude():
	try:
		current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script file path
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
		
		#walk through stub directory and add them to cip        
		stubList = [os.path.join(d, t) for d, ds, fs in os.walk(stubDir) for t in ds]
		for name in stubList:
			cipFile.write('-si "' + name + '"\n')
			cipFile.write('-q "' + name + '"\n')
		for fileName in stubList:
			if fileName.endswith("forceinclude"):
				fileList = [os.path.join(fileName, x) for x in os.listdir(fileName)]
				for fn in fileList:
					cipFile.write('-fi "' + fn + '"\n')

		compiler_path = os.getenv('AC6_HOME')

		if None == compiler_path:
			compiler_path = r'C:\TCC\Tools\armcompiler6\6.6.2_WIN64'

		compiler_include_path = [ 
			compiler_path + "\\include\\libcxx",
			compiler_path + "\\include"
		]

		for dirName in compiler_include_path:
			cipFile.write('-si "' + dirName + '"\n')
			cipFile.write('-q "' + dirName + '"\n')

		cipFile.close()
	except IOError: pass 

if __name__=="__main__":
	sysInclude()
