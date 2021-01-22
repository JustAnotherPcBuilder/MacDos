@echo off
CD /d "%~dp0"
:again
cls
python usbmaker.py
set /p choice="Program Finished, 'e' to exit or anything else to go again: "
if NOT '%choice%'=='e' goto again 