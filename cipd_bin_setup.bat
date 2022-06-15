@echo off
:: Copyright 2017 The Chromium Authors. All rights reserved.
:: Use of this source code is governed by a BSD-style license that can be
:: found in the LICENSE file.

call "%~dp0\cipd.bat" ensure -log-level warning -ensure-file "%~dp0\cipd_manifest.txt" -root "%~dp0\.cipd_bin"
:: copy ninja.exe to the root since many places assume ninja.exe exists in depot_tools.
:: TODO(crbug.com/931218): check in ninja.exe for now.
:: copy /y "%~dp0\.cipd_bin\ninja.exe" "%~dp0\ninja.exe" > nul
