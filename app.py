"""
Doc2Md - 文档批量转换为 Markdown 工具（V2 PySide6 桌面版）

支持格式: PDF（含扫描件 OCR、MinerU 高质量转换）/ Word / PPT / EPUB / TXT / HTML
支持拖拽文件/文件夹、整目录递归转换、保持原始目录结构。

入口：python app.py 或 python -m markitdown_gui
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# 日志配置（在导入其他模块前完成）
LOG_FILE = Path(__file__).parent / "doc2md.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("doc2md")

# 国内网络：HuggingFace 镜像 + 离线模式（MinerU 模型加载）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def main() -> int:
    """应用入口。"""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from core.config import ConfigManager
    from core.constants import APP_NAME, APP_VERSION
    from ui.main_window import MainWindow

    # 高 DPI 支持（Qt6 默认启用，显式设置确保兼容）
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Doc2Md")

    # 应用图标
    icon_path = Path(__file__).parent / "assets" / "icons" / "doc2md.icns"
    if not icon_path.exists():
        icon_path = Path(__file__).parent / "assets" / "icons" / "doc2md.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # 加载配置
    config = ConfigManager.load()

    # 主题
    if config.theme == "dark":
        app.setStyleSheet("QApplication { background-color: #2b2b2b; color: #e0e0e0; }")
    elif config.theme == "light":
        app.setStyleSheet("")

    logger.info(f"{APP_NAME} v{APP_VERSION} 启动")

    window = MainWindow(config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
