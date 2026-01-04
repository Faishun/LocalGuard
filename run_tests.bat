@echo off
echo Running tests with the active Python environment...
python -m pytest %*
echo All Tests Passed.
pause