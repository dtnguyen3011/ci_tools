@echo off
REM Do not setlocal in this file. All the varibles set here are to be global

set BUILD_DIR=%~dp0
set TOOLCOLLECTION=%1

call :run_install_tool_collection
call :run_initialize_tools_env

:run_install_tool_collection
    echo.
    echo Running InstallToolCollection to make sure we have all tools...
    echo.
    mkdir %BUILD_DIR%
    itc2 install %TOOLCOLLECTION% --tpdir %BUILD_DIR%
    call :check_error "Install tool collection failure"
goto:eof

:run_initialize_tools_env
    echo.
    echo Initializing tools environment...
    echo.
    call %BUILD_DIR%\TCC_ToolPaths.bat
    call :check_error "Tool's environment initialization failure"
goto:eof

:check_error
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: %1
    exit /b %ERRORLEVEL%
)
goto:eof