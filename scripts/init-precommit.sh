#!/bin/bash
set -e

# 이 스크립트는 pre-commit hooks를 설치하고 활성화합니다.
# 실패 시에는 아래 순서대로 직접 실행할 수 있습니다.
#   0) src 폴더로 이동
#      - `cd src`
#   1) 운영체제별 가상환경 활성화
#      - Linux/macOS: `source .venv/bin/activate`
#      - Windows(Git Bash/MSYS2): `source .venv/Scripts/activate`
#   2) pre-commit init
#      - `pre-commit install`

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting pre-commit setup..."
echo "📁 Project root: $PROJECT_ROOT"

# Change to project root directory
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo ""
    echo "❌ Error: Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "💡 Please create it first with one of:"
    echo "   uv venv"
    exit 1
fi

# Get OS name
OS="$(uname -s)"
echo "🖥️  Detected OS: $OS"

# Determine virtual environment activation script based on OS
if [[ "$OS" == "Linux" || "$OS" == "Darwin" ]]; then
    # Linux or macOS
    VENV_ACTIVATE=".venv/bin/activate"
elif [[ "$OS" == "MINGW"* || "$OS" == "MSYS"* || "$OS" == "CYGWIN"* ]]; then
    # Windows (Git Bash, MSYS2, Cygwin)
    VENV_ACTIVATE=".venv/Scripts/activate"
else
    echo ""
    echo "❌ Error: Unsupported OS: $OS"
    echo "💡 Supported: Linux, macOS (Darwin), Windows (MINGW/MSYS/CYGWIN)"
    exit 1
fi

# Check if activation script exists
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo ""
    echo "❌ Error: Activation script not found: $VENV_ACTIVATE"
    echo "💡 The virtual environment might be corrupted. Try recreating it."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_ACTIVATE"

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo ""
    echo "❌ Error: pre-commit is not installed in the virtual environment"
    echo "💡 Install it with: pip install pre-commit"
    exit 1
fi

# Display pre-commit version
PRE_COMMIT_VERSION=$(pre-commit --version)
echo "✅ Found pre-commit: $PRE_COMMIT_VERSION"
echo ""

# Initialize pre-commit hooks
echo "🔨 Installing pre-commit hooks..."
if pre-commit install; then
    echo "✅ Pre-commit hooks installed successfully"
else
    echo "❌ Error: Failed to install pre-commit hooks"
    exit 1
fi
echo ""