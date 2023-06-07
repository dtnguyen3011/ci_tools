import os, inspect
import sys
import platform



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
        print ">>>>> " + cipFilepath
        cipFile = open(cipFilepath, 'w')

        compiler_include_path = [ 
            r'C:\toolbase\greenhills_rel\comp_201815_1fp_x64\scxx',
            r'C:\toolbase\greenhills_rel\comp_201815_1fp_x64\include\v800',
            r'C:\toolbase\greenhills_rel\comp_201815_1fp_x64\ansi'
        ]
        stub_include_path = [
            os.path.join(dataDir,os.path.splitext(fileName.strip())[0],r'Stub\prlforceinclude'),
            os.path.join(dataDir,os.path.splitext(fileName.strip())[0],r'Stub')
        ]
        force_include_header = [
            os.path.join(dataDir,os.path.splitext(fileName.strip())[0],r'Stub\prlforceinclude\GH_RH_cpp.h'),
            os.path.join(dataDir,os.path.splitext(fileName.strip())[0],r'Stub\prlforceinclude\qacpp_reference_traits.h')
        ]
        for dirName in stub_include_path:
            cipFile.write('-si "' + dirName + '"\n')
            cipFile.write('-q "' + dirName + '"\n')
        for fn in force_include_header:
            cipFile.write('-fi "' + fn + '"\n')
        for dirName in compiler_include_path:
            cipFile.write('-si "' + dirName + '"\n')
            cipFile.write('-q "' + dirName + '"\n')

        cipFile.close()
    except IOError: pass 

if __name__=="__main__":
    if sys.platform == 'win32' :
        sysInclude()

