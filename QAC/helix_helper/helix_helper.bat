:: ----------------------------------------------------------------------------
:: Usage: Example script to use the helix_helper.py
:: =============================================================================
::   C O P Y R I G H T
:: -----------------------------------------------------------------------------
::   Copyright (c) 2018 by Robert Bosch GmbH. All rights reserved.
:: 
::   This file is property of Robert Bosch GmbH. Any unauthorized copy, use or
::   distribution is an offensive act against international law and may be
::   prosecuted under federal law. Its content is company confidential.
:: =============================================================================
::  Filename: helix_helper.bat
::  Author(s): Ingo Jauch CC-AD/ESW4 (Maintainer)
:: # ----------------------------------------------------------------------------

@echo off
set SCRIPTLOCATION=%~dp0

SET PROJECT_ROOT=%SCRIPTLOCATION%..\..\..\..
pushd %PROJECT_ROOT%
SET PROJECT_ROOT=%CD%
popd

echo "HELIX_HELPER BATCH"
echo "PROJECT_ROOT: " %PROJECT_ROOT%

:: Setup path to support run qt,qnx,cmake,cygwin and boost
SET PATH=C:\TCC\Tools\python3\3.6.5-6_WIN64;%PATH%	

SET DATASTORE_TARGET=default
echo.
IF [%1]==[] (
	echo "No commandline for 1st arg given, please choose a target from the datastore (e.g. helix_helper.json)"
	echo "Options:"
	echo "'jenkins_PR' analyze only on change files release1.5.1 (requires HELIX2019.2)"
	echo "'jenkins_ALL' analyze all files in project release1.5.1 (requires HELIX2019.2)"
	echo ---------------------------------------------
	EXIT 1
) ELSE (
	SET DATASTORE_TARGET=%1 & SET SUPPRESS_C_HEADER=--helper_suppress_c_header yes & SET PRQA_PATH="C:/TCC/Tools/helix_qac/2019.2-1_WIN64/common/bin"
)
echo "using datastore target: %DATASTORE_TARGET%"


SET HELPER_COMMAND="python3 %SCRIPTLOCATION%prqa_qaf/3rdpartytools/helix_helper/helix_helper.py --datastore_path %SCRIPTLOCATION%..\..\..\qaf_config/helix_helper/helix_helper.json --prqa_path %PRQA_PATH% --project_root %PROJECT_ROOT% --datastore_target %DATASTORE_TARGET% --helper_target"

SET OPTION=default
echo.
IF [%2]==[] (
	echo "No commandline for 2nd arg given, please choose a helper target:"
	echo "Options:"
	echo "1: create          (This option will create a new PRQA project for you (based on the aurix build))"
	echo "2: analyze         (This option will analyse an existing project (with all files in it))"
	echo "3: qaview          (This option will export an exsiting analysis to a spreadsheet)"
	echo "4: gui             (This option will start the gui for you and load the selected ruleset/project)"
	echo "5: list            (This option will require an existing PRQA project (from step 1.) and will analyse all files specified in the file qaf_config/helix_helper/helix_helper_file_list.txt)"
	echo "6: pr              (This option will require an existing PRQA project (from step 1.) and will analyse filles acording to the diff with the merge-base of your current branch)"
	echo "7: baseline_create (This option will require an existing PRQA project (from step 1.) and analyse (from step 2.) and creates a baseline)"
	echo "9: qavupload       (This option will upload existing analysis results to QAVerify)"
	echo "10: gen_changed_files (This option will generate file contain list of changed files)"
	SET /P OPTION="Choose: "
) ELSE (
	SET OPTION=%2
)

IF "%OPTION%"=="1" echo "1 selected" & CALL :create
IF "%OPTION%"=="2" echo "2 selected" & CALL :analyze
IF "%OPTION%"=="3" echo "3 selected" & CALL :qaview
IF "%OPTION%"=="4" echo "4 selected" & CALL :gui
IF "%OPTION%"=="5" echo "5 selected" & CALL :list
IF "%OPTION%"=="6" echo "6 selected" & CALL :pr
IF "%OPTION%"=="7" echo "7 selected" & CALL :baseline_create
IF "%OPTION%"=="9" echo "9 selected" & CALL :qavupload
IF "%OPTION%"=="10" echo "10 selected" & CALL :gen_changed_files
IF "%OPTION%"=="31" echo "31 selected" & CALL :state
echo "Error: Unknown option. %OPTION%"
pause >nul
EXIT 1

:create
echo "create function"
"%HELPER_COMMAND%" create %SUPPRESS_C_HEADER% --build_shell True %REMOVE_FILELIST%
CALL :done

:analyze
echo "analyze function"
"%HELPER_COMMAND%" analyze
CALL :done

:state
echo "state function"
"%HELPER_COMMAND%" state
CALL :done


:qaview
echo "export qaview"
"%HELPER_COMMAND%" qaview
CALL :done

:gui
echo "gui function"
"%HELPER_COMMAND%" gui
EXIT 0

:list
echo "list function"
"%HELPER_COMMAND%" analyze --analyse_list %SCRIPTLOCATION%..\..\..\qaf_config/helix_helper/helix_helper_file_list.txt
pause >nul
EXIT 0

:gen_changed_files
python.exe %SCRIPTLOCATION%prqa_qaf/3rdpartytools/find_cpps/find_cpps.py --cpp-result-amount all ^
--output_path %FIND_CPP_OUTPUT% ^
--prefixes %SCRIPTLOCATION%..\..\..\qaf_config/helix_helper/find_cpp_3rd_party_prefixes.txt ^
--from-list %FIND_CPP_INPUT_LIST% -v
CALL :done

:pr
IF %DATASTORE_TARGET%==jenkins_PR (
	echo "pr function jenkins"
	"%HELPER_COMMAND%" analyze --analyse_list %FIND_CPP_OUTPUT%
) ELSE (
	echo "pr function"
	python.exe %SCRIPTLOCATION%prqa_qaf/3rdpartytools/find_cpps/find_cpps.py --cpp-result-amount all ^
	--output_path %SCRIPTLOCATION%..\..\..\qaf_config/helix_helper/PR_changes_list.txt ^
    --prefixes %SCRIPTLOCATION%..\..\..\qaf_config/helix_helper/find_cpp_3rd_party_prefixes.txt ^
    -v
	"%HELPER_COMMAND%" analyze --analyse_list %SCRIPTLOCATION%..\..\..\qaf_config/helix_helper/PR_changes_list.txt
	pause >nul
)
EXIT 0

:baseline_create
echo "baseline_create function"
"%HELPER_COMMAND%" analyze --helper_create_baseline yes
CALL :done

:baseline_set
echo "baseline_set function"
echo "Specify path to baseline:"
SET /P BASELINE_PATH="Path: "
echo "using path: %BASELINE_PATH%" 
"%HELPER_COMMAND%" create --helper_set_baseline %BASELINE_PATH%
CALL :done

:qavupload
echo "qavupload function"
echo "environment variables needed:"
::SET QAV_PROJECT_NAME=pj_dc_int
::SET QAV_PROJECT_SNAPSHOT=fb83957c490d171a15ea3f6d2bb4a94e801ff9e7
SET QAV_SERVER_URL=https://abt-cc-da-qaverify.de.bosch.com:8091
::SET QAV_USERNAME=qavuser
::SET QAV_PASSWORD=qavpwd
SET QAV_UPLOAD_SOURCE=ALL
"%HELPER_COMMAND%" qavupload
CALL :done

:done
echo "Finished, press any key to return"
pause >nul
EXIT 0
