@echo off
setlocal

set TOOLCOLLECTION_XML=%1
echo %TOOLCOLLECTION_XML%

echo Running InstallToolCollection to make sure we have all tools...
set "TCC_COMMAND=%SystemRoot%\system32\WindowsPowerShell\v1.0\powershell.exe -file C:\TCC\Base\InstallToolCollection\InstallToolCollection.ps1"

%TCC_COMMAND% %TOOLCOLLECTION_XML% || goto ERROR
set "TPBAT=%TMP%\TCC_ToolPaths.bat"
%TCC_COMMAND% %TOOLCOLLECTION_XML% -GenerateToolPathBat %TPBAT% >NUL || goto ERROR
