@echo off
:: Copyright 2017 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

setlocal

set scriptdir=%~dp0

REM Set unique build ID.
FOR /f "usebackq tokens=*" %%a in (`python -c "import uuid; print(uuid.uuid4())"`) do set AUTONINJA_BUILD_ID=%%a

REM If a build performance summary has been requested then also set NINJA_STATUS
REM to trigger more verbose status updates. In particular this makes it possible
REM to see how quickly process creation is happening - often a critical clue on
REM Windows. The trailing space is intentional.
if "%NINJA_SUMMARIZE_BUILD%" == "1" set NINJA_STATUS=[%%r processes, %%f/%%t @ %%o/s : %%es ] 

:loop
IF NOT "%1"=="" (
    @rem Tell goma or reclient to not do network compiles.
    IF "%1"=="--offline" (
        SET GOMA_DISABLED=1
        SET RBE_remote_disabled=1
    )
    IF "%1"=="-o" (
        SET GOMA_DISABLED=1
        SET RBE_remote_disabled=1
    )
    SHIFT
    GOTO :loop
)

REM Execute whatever is printed by autoninja.py.
REM Also print it to reassure that the right settings are being used.
REM Don't use vpython - it is too slow to start.
REM Don't use python3 because it doesn't work in git bash on Windows and we
REM should be consistent between autoninja.bat and the autoninja script used by
REM git bash.
FOR /f "usebackq tokens=*" %%a in (`python %scriptdir%autoninja.py "%*"`) do echo %%a & %%a
@if errorlevel 1 goto buildfailure

REM Use call to invoke python script here, because we use python via python.bat.
@if "%NINJA_SUMMARIZE_BUILD%" == "1" call python %scriptdir%post_build_ninja_summary.py %*
@call python %scriptdir%ninjalog_uploader_wrapper.py --cmdline %*

exit /b
:buildfailure

@call python %scriptdir%ninjalog_uploader_wrapper.py --cmdline %*

REM Return an error code of 1 so that if a developer types:
REM "autoninja chrome && chrome" then chrome won't run if the build fails.
cmd /c exit 1
