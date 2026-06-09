@echo off
REM Universal DeNoiser Windows Executable Wrapper
REM This allows you to run 'denoiser <command>' from anywhere on your system
REM assuming this folder is added to your Windows PATH.

python "%~dp0cli.py" %*
