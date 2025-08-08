@echo off
echo Starting Flask server with debug output...
echo.
echo Server logs will be saved to server_debug.log
echo Press Ctrl+C to stop the server
echo.
py main.py > server_debug.log 2>&1