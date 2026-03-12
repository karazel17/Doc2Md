#!/bin/bash
# ============================================================
#  Doc2Md 启动脚本
#  双击此文件或在终端运行即可启动
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# 检查是否已安装
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "  首次使用，需要先安装依赖..."
    echo "  正在运行安装脚本..."
    echo ""
    bash "$SCRIPT_DIR/install.sh"

    # 安装后再次检查
    if [ ! -d "$VENV_DIR" ]; then
        echo "安装失败，请手动运行 install.sh"
        exit 1
    fi
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 设置 HuggingFace 镜像（国内网络适用）
export HF_ENDPOINT=https://hf-mirror.com
export TRANSFORMERS_OFFLINE=1

# 启动应用
echo ""
echo "=================================================="
echo "  Doc2Md 正在启动..."
echo "  浏览器将自动打开"
echo "  如未自动打开，请手动访问: http://127.0.0.1:7860"
echo "  按 Ctrl+C 停止程序"
echo "=================================================="
echo ""

cd "$SCRIPT_DIR"
python3 app.py
