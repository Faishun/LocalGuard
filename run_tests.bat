@echo off
echo Running tests with the active Python environment...
python -m pytest %*
if %ERRORLEVEL% NEQ 0 (
    echo Tests Failed!
    exit /b %ERRORLEVEL%
)
echo All Tests Passed.
pause