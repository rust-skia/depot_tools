@echo off
:: Copyright 2022 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.
setlocal

set scriptdir=%~dp0

:: Ensure that "depot_tools" is somewhere in PATH so this tool can be used
:: standalone, but allow other PATH manipulations to take priority.
set PATH=%PATH%;%scriptdir%

:: Defer control.
call %scriptdir%python-bin\python3.bat "%~dp0\ninja.py" %*
