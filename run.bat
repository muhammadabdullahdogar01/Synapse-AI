@echo off
REM One-click launcher for SYNAPSE AI
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Setting up for the first time...
    python -m venv venv || (echo Python is not installed. Get it from python.org & pause & exit /b 1)
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

where ollama >nul 2>nul
if errorlevel 1 (
    echo WARNING: Ollama is not installed. AI features will be offline.
    echo Download it from https://ollama.com
) else (
    ollama list >nul 2>nul || (echo Starting Ollama... & start "" /min ollama serve & timeout /t 3 >nul)
    ollama list | findstr /c:"qwen3:4b" >nul || (echo Downloading the AI model, first time only... & ollama pull qwen3:4b-instruct)
    ollama list | findstr /c:"nomic-embed-text" >nul || (echo Downloading the search model, first time only... & ollama pull nomic-embed-text)
)

echo Starting SYNAPSE AI...
venv\Scripts\python.exe -m streamlit run main.py
