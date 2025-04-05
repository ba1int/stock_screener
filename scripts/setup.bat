@echo off
REM Setup script for the stock screener on Windows

REM Create required directories
if not exist component_results mkdir component_results
if not exist test_results mkdir test_results
if not exist stock_screener\data\results mkdir stock_screener\data\results

REM Copy environment file if it doesn't exist
if not exist .env (
    copy .env.example .env
    echo Created .env file from template. Please update with your API keys.
) else (
    echo .env file already exists.
)

REM Install dependencies
pip install -r requirements.txt

echo Setup complete! 