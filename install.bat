@echo off
REM ===========================================================================
REM  Writing System - one-click installer
REM  Double-click this file to install the skill and start setup.
REM  Requires: Claude Code (https://claude.ai/code) and Docker Desktop running.
REM ===========================================================================
title Writing System Installer
echo.
echo  ============================================================
echo    Writing System - Installer
echo  ============================================================
echo.

REM --- Is Claude Code installed and on PATH? ---
where claude >nul 2>&1
if errorlevel 1 (
  echo  Claude Code was not found on this computer.
  echo.
  echo  Please install it first from:  https://claude.ai/code
  echo  Then double-click this file again.
  echo.
  pause
  exit /b 1
)

REM --- Friendly heads-up about Docker ---
echo  Before we start, make sure Docker Desktop is running
echo  (look for the whale icon near your clock). The setup needs it.
echo.
echo  Press any key to install the Writing System skill...
pause >nul
echo.

echo  Installing the skill from GitHub...
call claude skill install https://github.com/elf1024-vot/writing-docket
if errorlevel 1 (
  echo.
  echo  The skill install did not complete. If it mentioned Git, install Git from
  echo  https://git-scm.com/download/win and run this file again.
  echo.
  pause
  exit /b 1
)

echo.
echo  ------------------------------------------------------------
echo   Skill installed. Claude Code will open now.
echo.
echo   In the window that opens, type this and press Enter:
echo.
echo        /start-here
echo.
echo   It will ask you a few simple questions, then build your
echo   writing system for you. Leave the window open until you
echo   see "Setup Complete".
echo  ------------------------------------------------------------
echo.
pause
call claude
