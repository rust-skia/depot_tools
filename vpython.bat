@echo off
:: Copyright 2017 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

:: See revert instructions in cipd_manifest.txt

:: Note: we set EnableDelayedExpansion so we can perform string manipulations
:: in our arguments parsing loop. This only works on Windows XP+.
setlocal EnableDelayedExpansion

if "%VPYTHON_BYPASS%"=="manually managed python not supported by chrome operations" (
  set "arguments="
  set "ignore="
  set "stop="
  for %%x in (%*) do (
    set "arg=%%x"

    if defined stop (
      set "arguments=!arguments! %%~x"
    ) else (
      if "!arg!"=="--" (
        set "stop=1"
      ) else (
        :: These tools all do something vpython related and quit
        if "!arg:~0,13!"=="-vpython-tool" (
          goto :END
        )

        :: Delete any vpython specific flag
        if "!arg:~0,8!"=="-vpython" (
          set "ignore=1"
        ) else (
          if defined ignore (
            set "ignore="
          ) else (
            set "arguments=!arguments! %%~x"
          )
        )
      )
    )
  )

  call "python" !arguments!
  if errorlevel 1 goto :END
)

call "%~dp0\cipd_bin_setup.bat" > nul 2>&1
"%~dp0\.cipd_bin\vpython.exe" -vpython-interpreter "%~dp0\python.bat" %*

:END
endlocal
exit /b %ERRORLEVEL%
