#!/bin/bash
# ============================================================
#  Doc2Md 一键安装脚本 (macOS / Linux)
#
#  此脚本会:
#  1. 检查 Python 环境
#  2. 创建虚拟环境
#  3. 安装基础依赖
#  4. 可选安装 MinerU (高质量PDF转换)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo ""
echo "=================================================="
echo "  Doc2Md 安装程序"
echo "=================================================="
echo ""

# ── 1. 检查 Python ──
echo "[1/4] 检查 Python 环境..."

PYTHON_CMD=""
for cmd in python3.11 python3.10 python3.12 python3; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 9 ] && [ "$minor" -le 12 ]; then
            PYTHON_CMD="$cmd"
            echo "  找到 Python: $($cmd --version)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "  未找到 Python 3.9 - 3.12"
    echo ""
    echo "  请先安装 Python:"
    echo "    方法1 (推荐): brew install python@3.11"
    echo "    方法2: 从 https://www.python.org/downloads/ 下载安装"
    echo ""
    exit 1
fi

# ── 2. 创建虚拟环境 ──
echo ""
echo "[2/4] 创建虚拟环境..."

if [ -d "$VENV_DIR" ]; then
    echo "  虚拟环境已存在，跳过创建"
else
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "  虚拟环境已创建: $VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 升级 pip
pip install --upgrade pip -q

# ── 3. 安装基础依赖 ──
echo ""
echo "[3/4] 安装基础依赖（首次安装可能需要几分钟）..."

pip install -r "$SCRIPT_DIR/requirements.txt" -q

echo "  基础依赖安装完成"

# ── 4. 可选安装 MinerU ──
echo ""
echo "[4/4] MinerU 安装（可选，用于高质量PDF转换）"
echo ""
echo "  MinerU 可以更好地处理："
echo "    - 复杂排版的PDF"
echo "    - 包含表格和公式的文档"
echo "    - 扫描件PDF的文字识别"
echo ""

read -p "  是否安装 MinerU？(y/N): " install_mineru

if [[ "$install_mineru" =~ ^[Yy]$ ]]; then
    echo ""
    echo "  正在安装 MinerU（可能需要较长时间）..."
    pip install "magic-pdf[full]" -q 2>&1 | tail -5

    echo ""
    echo "  正在下载 MinerU 模型文件..."

    # 创建模型目录
    MODELS_DIR="$HOME/.doc2md_models"
    mkdir -p "$MODELS_DIR"

    # 下载模型配置
    if command -v magic-pdf &> /dev/null; then
        # 尝试初始化 MinerU，它会自动下载模型
        echo "  MinerU 安装成功！"
        echo "  首次使用时会自动下载所需的模型文件。"
    else
        echo "  MinerU 安装可能未完全成功，但不影响基础功能的使用。"
        echo "  您可以稍后手动安装: pip install \"magic-pdf[full]\""
    fi
else
    echo "  跳过 MinerU 安装"
    echo "  您随时可以手动安装: "
    echo "    source venv/bin/activate && pip install \"magic-pdf[full]\""
fi

# ── 完成 ──
echo ""
echo "=================================================="
echo "  安装完成！"
echo "=================================================="
echo ""
echo "  启动方法:"
echo "    双击 start.sh 或在终端运行:"
echo "    cd \"$SCRIPT_DIR\" && ./start.sh"
echo ""
echo "  程序启动后会自动打开浏览器。"
echo ""
