@echo off
setlocal enabledelayedexpansion

rem LinguaBridge Docker Build Script

rem Project Info
set REPO=mimitoou114
set PROJECT_NAME=linguabridge
set IMAGE_NAME=linguabridge-app
if "%~1"=="" (
    set VERSION=latest
) else (
    set VERSION=%~1
)

echo === LinguaBridge Docker Build Script ===
echo Repo: %REPO%
echo Project Name: %PROJECT_NAME%
echo Image Name: %IMAGE_NAME%
echo Version Tag: %VERSION%
echo.

rem Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH
    exit /b 1
)

rem Check if docker-compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Warning: docker-compose not installed, will only build image
    set COMPOSE_AVAILABLE=false
) else (
    set COMPOSE_AVAILABLE=true
)

rem Create necessary directories
echo Creating necessary directories...
if not exist output mkdir output
if not exist logs mkdir logs

rem Build Docker image
echo Building Docker image...
docker build -t %REPO%/%IMAGE_NAME%:%VERSION% .

if errorlevel 1 (
    echo X Docker image build failed
    exit /b 1
) else (
    echo + Docker image build successful
)

rem Tag as latest if version is not latest
if not "%VERSION%"=="latest" (
    docker tag %REPO%/%IMAGE_NAME%:%VERSION% %REPO%/%IMAGE_NAME%:latest
    echo + Image tagged as latest
)

rem Show image info
echo Image info:
docker images | findstr %IMAGE_NAME%

echo.
echo === Build Complete ===
echo Use the following command to run container:
echo docker run -p 8000:8000 %REPO%/%IMAGE_NAME%:%VERSION%
echo.
pause
