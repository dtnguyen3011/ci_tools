@echo off
set repoDir=%1

pushd %repoDir%
for /f "delims=" %%a in ('git remote get-url --push origin') do set git_remote_url=%%a
if "%git_remote_url%"=="" (
    set git_remote_url="ssh://git@sourcecode01.de.bosch.com:7999/vwag_e3/commonrepo.git"
)
CALL :ExcuteCommand del /S *.lock || GOTO FreshClone
CALL :ExcuteCommand git checkout -f develop || GOTO FreshClone
CALL :ExcuteCommand git reset --hard origin/develop || GOTO FreshClone
CALL :ExcuteCommand git clean -xffd || GOTO FreshClone
CALL :ExcuteCommand git fetch -p --recurse-submodules=no origin develop || GOTO FreshClone
CALL :ExcuteCommand git pull || GOTO FreshClone
CALL :ExcuteCommand git gc --prune=now || GOTO FreshClone
CALL :ExcuteCommand git remote prune origin || GOTO FreshClone
CALL :ExcuteCommand git pull || GOTO FreshClone
CALL :ExcuteCommand git fetch -p --recurse-submodules=no origin develop || GOTO FreshClone
CALL :ExcuteCommand git lfs fetch --recent || GOTO FreshClone
CALL :ExcuteCommand git submodule sync --recursive || GOTO FreshClone
CALL :ExcuteCommand git submodule foreach --recursive "git reset --hard HEAD && git clean -xffd" || GOTO FreshClone
CALL :ExcuteCommand git submodule foreach --recursive "git gc --prune=now && git remote prune origin" || GOTO FreshClone
CALL :ExcuteCommand git submodule update --init --recursive --force || GOTO FreshClone
CALL :ExcuteCommand git submodule foreach --recursive "git lfs fetch --recent" || GOTO FreshClone
popd
GOTO End

:FreshClone
echo %computername% --- FreshClone with git_remote_url %git_remote_url%
CALL :ExcuteCommand rmdir /s /q .
CALL :ExcuteCommand git clone %git_remote_url% -b develop . || EXIT /B %ERRORLEVEL%
CALL :ExcuteCommand git lfs fetch --recent || EXIT /B %ERRORLEVEL%
CALL :ExcuteCommand git submodule sync --recursive || EXIT /B %ERRORLEVEL%
CALL :ExcuteCommand git submodule foreach --recursive "git reset --hard HEAD && git clean -xffd" || EXIT /B %ERRORLEVEL%
CALL :ExcuteCommand git submodule foreach --recursive "git gc --prune=now && git remote prune origin" || EXIT /B %ERRORLEVEL%
CALL :ExcuteCommand git submodule update --init --recursive --force || EXIT /B %ERRORLEVEL%
CALL :ExcuteCommand git submodule foreach --recursive "git lfs fetch --recent" || EXIT /B %ERRORLEVEL%
echo %computername% --- ~FreshClone
GOTO End

:ExcuteCommand
set startTime=%time%
set gitCommand=%*
echo %computername% --- %gitCommand% --- : startTime at %startTime%
%gitCommand%
set errorCode=%ERRORLEVEL%
set endTime=%time%
CALL :TimeCalculate "%startTime%" "%endTime%" timeDiff
set outPutStr=%computername% --- ~%gitCommand% --- : %startTime% - %endTime% - %timeDiff%
if %errorCode% neq 0 (
    set outPutStr=%outPutStr% --- FAILURE with ERRORLEVEL %errorCode%
)
echo %outPutStr%
EXIT /B %errorCode%

:TimeCalculate
setlocal EnableDelayedExpansion
set "sTime=%~1"
set "eTime=%~2"
rem Convert the start and end times into seconds
set /a sTimeInSeconds=!sTime:~0,2! * 3600 + !sTime:~3,2! * 60 + !sTime:~6,2!
set /a eTimeInSeconds=!eTime:~0,2! * 3600 + !eTime:~3,2! * 60 + !eTime:~6,2!
rem Calculate the time difference in seconds
set /a timeDiffInSeconds=%eTimeInSeconds% - %sTimeInSeconds%
rem Convert the time difference back into hours, minutes, and seconds format
set /a hours=%timeDiffInSeconds% / 3600
set /a minutes=(%timeDiffInSeconds% - %hours% * 3600) / 60
set /a seconds=%timeDiffInSeconds% - %hours% * 3600 - %minutes% * 60
rem Output the result
endlocal & set "%~3=took %hours%h%minutes%m%seconds%s"
EXIT /B 0

:End
echo "UPDATE REPO %repoDir% FINISHED WITH RESULT SUCCESS"
EXIT /B 0
