#!/bin/bash

# 이 스크립트는 uv 기반 가상환경을 자동으로 활성화·동기화합니다.
# 실패 시에는 아래 순서대로 직접 실행할 수 있습니다.
#   0) uv가 없다면 설치
#   1) .venv 폴더가 없다면 `uv venv`로 .venv 폴더를 생성
#   2) 운영체제별 가상환경 활성화
#      - Linux/macOS: `source .venv/bin/activate`
#      - Windows(Git Bash/MSYS2): `source .venv/Scripts/activate`
#   3) `uv sync`로 의존성 동기화

# Assume user runs this from SafeHome or SafeHome/src
CURRENT_DIR=$(pwd)
CURRENT_DIR_NAME="${CURRENT_DIR##*/}"

# If current directory is not src, try to move to src
if [ "$CURRENT_DIR_NAME" != "src" ]; then
    if [ -d "src" ]; then
        cd src
    else
        echo "Error: 'src' directory not found. Please run from SafeHome or SafeHome/src"
        exit 1
    fi
fi

PROJECT_ROOT=$(pwd)
echo "Project root: $PROJECT_ROOT"

# Detect OS
OS="$(uname -s)"

# deactivate venv if it is active
if [ -n "$VIRTUAL_ENV" ]; then
    echo "deactivating venv"
    deactivate
fi

# deactivate conda environment if it is active
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "deactivating conda environment"
    conda deactivate || true
fi

# check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv could not be found"
    exit 1
fi

# check if .venv exists in project root
VENV_PATH="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo ".venv not found in project root, creating..."
    (cd "$PROJECT_ROOT" && uv venv)
else
    echo ".venv found in project root"
fi

# activate venv based on OS
echo "Activating .venv..."
if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    source "$VENV_PATH/bin/activate"
elif [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* || "$OS" == "CYGWIN"* ]]; then
    source "$VENV_PATH/Scripts/activate"
else
    echo "Unsupported OS: $OS"
    exit 1
fi

# sync dependencies
echo "Syncing dependencies..."
uv sync
