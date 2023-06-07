@echo off
set SCRIPTLOCATION=%~dp0
set PROJECT_ROOT=%SCRIPTLOCATION%..\..\..\..
pushd %PROJECT_ROOT%
set PRQA_DIR=%1

rmdir /s /q %PRQA_DIR%\prqa\configs\Initial\output
mkdir %PRQA_DIR%\publish
( robocopy %PRQA_DIR% %PRQA_DIR%\publish qacli-view-summary.html /MOVE ) ^& IF %ERRORLEVEL% LEQ 1 exit 0
