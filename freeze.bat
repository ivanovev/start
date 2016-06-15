@echo off
Setlocal EnableDelayedExpansion
set name=start
set srcdir=C:\Share\%name%
set s7z="C:\Program Files\7-Zip\7z.exe"
set pyinst="C:\Python35\Scripts\pyinstaller.exe"

rmdir /S /Q build dist __pycache__

set all=hm br fio tmb all
set /p id="%all%: " %=%
if not "%id%" == "all" (
	set all=%id%
)
set hiddenimport=
for /f %%i in ('dir /b /o:n /ad') do set hiddenimport=!hiddenimport! --hiddenimport %%i
for %%a in (%all%) do (
	if not "%%a" == "all" (
		copy %%a\start%%a.py start%%a.py
		set import=--hiddenimport ctl
	) else (
		set import=%hiddenimport%
	)
	cmd /C %pyinst% --onefile !import! start%%a.py
	del /F "%srcdir%\%%a.7z"
	cd dist
	%s7z% a "%srcdir%\%%a.7z" start%%a.exe
	cd ..
)
pause
