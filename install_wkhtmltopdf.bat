@echo off
echo Installing wkhtmltopdf...
curl -L https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.msvc2015-win64.exe -o wkhtmltox.exe
start /wait wkhtmltox.exe /silent /verysilent /norestart
del wkhtmltox.exe
echo Installation complete.
