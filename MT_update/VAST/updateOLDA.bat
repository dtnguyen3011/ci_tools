@echo off
echo =======================================================================================================================
echo \                                             updateOLDA.bat                                                        \
echo \                                                                                                                     \
echo \ @brief: this script is to automate VAST cml tooling for Jenkins to update olda                                      \
echo \ @Usage: $ VastCml.bat { A2L-Dir A2L-DB --OLDA OldaCopyList                                                          \
echo \ @Where:                                                                                                             \
echo \        A2L-Dir              : path to directory holding A2L DB to be update [e.g. C:\temp\]                         \
echo \        A2L-DB               : file holding A2L Database [e.g. RadarFC.a2l]                                          \
echo \        OldaCopyList         : file holding Signal IDs to be recorded by Vector OLDA copy [e.g. OldaList.txt]        \
echo \ @author: Pham Ngoc Thai (RBVH/EDA15)                                                                                \
echo \ @copyright: Robert Bosch GmbH, 2020                                                                                 \
echo =======================================================================================================================

SETLOCAL EnableDelayedExpansion
set W_ERROR=0

:parseArgs
	if "%~1"=="" (
        goto :start
	)
	if "%~1"=="--tmp" (
		SET a2l_dir=%~2\MTPlanProc\delivery\Measurement\database\a2l
	)
	if "%~1"=="--oldalist" (
        SET oldaCopyList=%~2
	)
	shift
	goto :parseArgs

:start
REM Check whether all required environment variables have been set by the calling build script
set "NEEDED_ENV_VARS=a2l_dir, oldaCopyList"
for %%v in (%NEEDED_ENV_VARS%) do (
	if not defined %%v set W_ERROR=1
)
if %W_ERROR% EQU 1 goto :error

echo vastCml.bat will be started now...

pushd \\bosch.com\dfsrb\DfsDE\DIV\CS\DE_CS$\Prj\DA\Dev_Tools\03_Common\VAST\Resource

vastCml.bat %a2l_dir% RadarFC.a2l --OLDA %oldaCopyList%

exit /b

:error
if %W_ERROR% EQU 1 echo Error: This script require 2 parameters to update olda
exit /b %W_ERROR%