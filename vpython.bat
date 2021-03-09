@echo off
:: Copyright 2017 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

:: TODO(crbug.com/1003139): Remove.
:: Add Python 3 to PATH to work around crbug.com/1003139.
for /f %%i in (%~dp0python_bin_reldir.txt) do set PYTHON2_BIN_RELDIR=%%i
set PATH=%~dp0%PYTHON2_BIN_RELDIR%;%~dp0%PYTHON2_BIN_RELDIR%\Scripts;%~dp0%PYTHON2_BIN_RELDIR%\DLLs;%PATH%

call "%~dp0\cipd_bin_setup.bat" > nul 2>&1
"%~dp0\.cipd_bin\vpython.exe" -vpython-interpreter "%~dp0\%PYTHON2_BIN_RELDIR%\python.exe" %*
