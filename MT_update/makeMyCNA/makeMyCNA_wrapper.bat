@echo off
echo =======================================================================================================================
echo \                                             makeMyCNA_wrapper.bat                                                   \
echo \                                                                                                                     \
echo \ @brief: the script can be used to automate makeMyCNA for Jenkins without adapting paths in the init file            \
echo \         makeMyCNA_local.ini. If you want to use the deault path in the init file, just run this script              \
echo \         without input argument.                                                                                     \
echo \         4 paths can be adapted: path to RadarFC.cna (mandatory), path to scom_gen (mandatory),                      \
echo \                                 path to CANAPE (optional), path to temp folder (optional)                           \
echo \ @Usage: makeMyCNA_wrapper.bat -m [path to RadarFC.cna] -s [path to scom_gen] -e [path to elf]                       \
echo \ @Usage: makeMyCNA_wrapper.bat -m [path to RadarFC.cna] -s [path to scom_gen] -e [path to elf]                       \
echo \                                 --canape [path to CANAPE] --temp [path to temp folder]                              \
echo \                                 --list [path to customer list]                                                      \
echo \                                 -h or --h or help for more info                                                     \
echo \ @author: Pham Ngoc Thai (RBVH/EDA15)                                                                                \
echo \ @copyright: Robert Bosch GmbH, 2020                                                                                 \
echo =======================================================================================================================

SETLOCAL EnableDelayedExpansion
SET mypath=%~dp0

echo Call TCC tool initialization script to init the environment
pushd .\..\..\..\..\..\..\tools_common\build_tools\tcc
if exist TCC_ToolPaths.bat call TCC_ToolPaths.bat
if not exist TCC_ToolPaths.bat call tcc_tools.bat
popd


set PHYTON_3_TCC_EXE=%TCCPATH_python3%\python.exe

rem check input argument
set argCount=0
for %%x in (%*) do (
   set /A argCount+=1
)

if %argCount% LSS 1 (
	echo No arguments given, default paths in makeMyCNA_local.ini will be used!
	copy %mypath%\makeMyCNA_local.ini %mypath%\makeMyCNA_local_cust.ini
	goto makeMyCNA
)

:parseArgs
	if "%~1"=="" (
		goto :start
	)
	if "%~1"=="-m" (
		set path_mt=%~2
	)
	if "%~1"=="-s" (
		set path_scom=%~2
	)
	if "%~1"=="-e" (
		set path_elf=%~2
	)
	if "%~1"=="-c" (
		set path_canape="-c" %2
	)
	if "%~1"=="-t" (
		set path_temp="-t" %2
	)
	if "%~1"=="-l" (
		set path_list="-l" %2
	)
	if "%~1"=="-p" (
		set prj_name="-p" %2
	)
	if "%~1"=="-h" (
		goto help
	)
	shift
	goto parseArgs

:start
%PHYTON_3_TCC_EXE% %mypath%\adapt_paths.py -m %path_mt% -s %path_scom% -e %path_elf% %path_canape% %path_temp% %path_list% %prj_name%
echo.
echo ---------------------------------------------------
echo Generated makeMyCNA_local_cust.ini successfully!!!

set path_mt=
set path_scom=
set path_elf=
set path_canape=
set path_temp=
set path_list=
goto makeMyCNA

:help
%PHYTON_3_TCC_EXE% %mypath%\adapt_paths.py -h
goto :eof

:makeMyCNA
echo ---------------- ini - file -----------------------
type makeMyCNA_local_cust.ini
echo ---------------------------------------------------
echo makeMyCNA_Jenkins.bat will be started now...

pushd \\bosch.com\dfsrb\DfsDE\DIV\CS\DE_CS$\Prj\DA\Dev_Tools\03_Common\MakeMyCNA\Resource

makeMyCNA_Jenkins.bat %mypath%makeMyCNA_local_cust.ini

echo %ERRORLEVEL%