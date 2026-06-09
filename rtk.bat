@echo off
REM Universal RTK Engine Windows Executable Wrapper
REM This allows you to run 'rtk <command>' from anywhere on your system
REM assuming this folder is added to your Windows PATH.

python "%~dp0cli.py" %*
