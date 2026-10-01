@echo off
chcp 65001 >nul
title Տենդերային մոնիտոր - ՏԵԱԴՈՒՄ
echo ============================================
echo   Տենդերային մոնիտոր - գրադարանների տեղադրում
echo ============================================
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"
echo.
echo Պատրաստ է։ Այժմ գործարկեք RUN.bat ֆայլը։
pause
