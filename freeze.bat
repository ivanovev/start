@echo off
Setlocal EnableDelayedExpansion
set name=start
set srcdir=C:\Share\start
set srctgz="%srcdir%\%name%.tgz"
set srctar=%name%.tar
set s7z="C:\Program Files\7-Zip\7z.exe"
set cxfreeze="C:\Python33\Scripts\cxfreeze.bat"

rmdir /S /Q freeze
del "%srcdir%\*.7z"

%s7z% x "%srctgz%" -ofreeze
cd freeze
%s7z% x "%srctar%"

set all=hm all
set /p id="hm/all: " %=%
if not "%id%" == "all" (
	set all=%id%
)
set allmodules=
for /f %%i in ('dir /b /o:n /ad') do set allmodules=!allmodules!,%%i
set allmodules=%allmodules:~1%
echo %allmodules%
set modules=
for %%a in (%all%) do (
	if not "%%a" == "all" (
		copy %%a\start%%a.py start%%a.py
		set modules=%%a
	) else (
		set modules=%allmodules%
	)
	cmd /C %cxfreeze% start%%a.py --include-modules=!modules! --target-dir=dist%%a
	del /F "%srcdir%\%%a.7z"
	cd dist%%a
	%s7z% a "%srcdir%\%%a.7z" *
	cd ..
)
pause
