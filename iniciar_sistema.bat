@echo off
title Sistema Devocional KDP - 30 Dias
cd /d "%~dp0"
echo ========================================================
echo        SISTEMA GERADOR DE DEVOCIONAL KDP (AMAZON)
echo ========================================================
echo.
echo Iniciando painel de controle e visualizacao...
echo.
streamlit run app.py
pause
