@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto missing
".venv\Scripts\python.exe" -c "import langgraph.graph" >nul 2>&1
if errorlevel 1 goto missing
".venv\Scripts\python.exe" app.py
pause
exit /b
:missing
echo Run cai-dat.cmd first to install LangGraph.
pause
exit /b 1
