@echo Off

set PATHTOSCRIPT=%1
set BUILDPATH=%2
set BUILDVARIANT=%3

call perl %PATHTOSCRIPT%\check_mem_C2_L_device.pl %BUILDPATH%\%BUILDVARIANT%.map > ./check_mem_%BUILDVARIANT%_check.txt
rem copy RAM ROM report to artifactory
robocopy .\ %BUILDPATH% check_mem_%BUILDVARIANT%_check.txt 
rem pause