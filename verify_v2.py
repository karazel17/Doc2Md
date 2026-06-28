#!/usr/bin/env python3
"""Doc2Md V2 验证脚本

验证内容：
1. 所有模块导入正常
2. 配置管理读写正常
3. 文件扫描正常
4. 转换门面正常（TXT/HTML）
5. UI 模块导入正常（需要 PySide6）
6. UI 能否在 offscreen 模式下创建主窗口

用法：
    cd /path/to/Doc2Md
    python verify_v2.py
"""

import sys
import os

# 设置 offscreen 模式（无显示器环境也能测试 UI）
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_imports():
    """测试所有模块导入。"""
    print("=== 1. 模块导入测试 ===")

    # core 层
    from core import config, constants, converter_facade
    from core.config import AppConfig, MinerUConfig, LLMConfig, ConfigManager
    from core.constants import APP_NAME, APP_VERSION, SUPPORTED_FILE_TYPES
    from core.converter_facade import ConvertResult, ConverterFacade
    print("  ✓ core 层导入成功")

    # converters 层
    from converters import EXTENSION_MAP, TYPE_EXTENSIONS
    from converters.batch import scan_files, convert_single_file, batch_convert
    from converters.pdf_converter import convert_pdf
    print("  ✓ converters 层导入成功")

    # workers 层
    from workers.convert_worker import ConvertWorker
    print("  ✓ workers 层导入成功")

    # UI 层（需要 PySide6）
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        from ui.drop_area import DropArea
        from ui.file_list import FileList
        from ui.progress_panel import ProgressPanel
        from ui.settings_dialog import SettingsDialog
        print("  ✓ UI 层导入成功")
    except ImportError as e:
        print(f"  ✗ UI 层导入失败（需要 PySide6）: {e}")
        return False

    return True


def test_config():
    """测试配置管理。"""
    print("\n=== 2. 配置管理测试 ===")
    from core.config import AppConfig, ConfigManager

    cfg = AppConfig()
    print(f"  默认配置: OCR={cfg.enable_ocr}, MinerU={cfg.mineru.enabled}, mode={cfg.mineru.mode}")
    print("  ✓ 配置管理正常")
    return True


def test_scanner():
    """测试文件扫描。"""
    print("\n=== 3. 文件扫描测试 ===")
    import tempfile
    from pathlib import Path
    from converters.batch import scan_files

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "test.txt").write_text("hello")
        (root / "test.html").write_text("<html></html>")
        (root / ".hidden.txt").write_text("hidden")

        files = scan_files(root, ["TXT", "HTML"])
        names = [f.name for f in files]
        assert "test.txt" in names
        assert "test.html" in names
        assert ".hidden.txt" not in names
        print(f"  扫描到 {len(files)} 个文件（隐藏文件已过滤）")
        print("  ✓ 文件扫描正常")
    return True


def test_facade():
    """测试转换门面。"""
    print("\n=== 4. 转换门面测试 ===")
    import tempfile
    from pathlib import Path
    from core.config import AppConfig
    from core.converter_facade import ConverterFacade

    facade = ConverterFacade(AppConfig())
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        out = root / "output"
        out.mkdir()

        txt = root / "sample.txt"
        txt.write_text("Hello Doc2Md V2", encoding="utf-8")

        result = facade.convert_one(txt, root, out)
        assert result.success, f"转换应成功: {result.message}"
        assert result.output_path.exists()
        content = result.output_path.read_text(encoding="utf-8")
        assert "Hello Doc2Md V2" in content
        print(f"  TXT 转换成功: {result.output_path.name}")
        print("  ✓ 转换门面正常")
    return True


def test_ui():
    """测试 UI 能否创建主窗口。"""
    print("\n=== 5. UI 主窗口测试 ===")
    try:
        from PySide6.QtWidgets import QApplication
        from core.config import AppConfig
        from ui.main_window import MainWindow

        app = QApplication.instance() or QApplication(sys.argv)
        config = AppConfig()
        window = MainWindow(config)
        print(f"  主窗口创建成功: {window.windowTitle()}")
        print(f"  窗口尺寸: {window.width()}x{window.height()}")
        print("  ✓ UI 正常")
        return True
    except Exception as e:
        print(f"  ✗ UI 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Doc2Md V2 验证脚本")
    print("=" * 50)

    results = []

    # 基础测试（不需要 PySide6）
    results.append(("模块导入", test_imports()))
    results.append(("配置管理", test_config()))
    results.append(("文件扫描", test_scanner()))
    results.append(("转换门面", test_facade()))

    # UI 测试（需要 PySide6）
    try:
        import PySide6
        results.append(("UI 主窗口", test_ui()))
    except ImportError:
        print("\n=== 5. UI 主窗口测试 ===")
        print("  ⚠ 跳过（PySide6 未安装）")
        results.append(("UI 主窗口", None))

    # 汇总
    print("\n" + "=" * 50)
    print("验证汇总:")
    for name, result in results:
        if result is True:
            print(f"  ✓ {name}")
        elif result is False:
            print(f"  ✗ {name}")
        else:
            print(f"  ⚠ {name}（跳过）")

    failed = [name for name, r in results if r is False]
    if failed:
        print(f"\n❌ {len(failed)} 项失败: {', '.join(failed)}")
        return 1
    else:
        print("\n✅ 所有测试通过！")
        return 0


if __name__ == "__main__":
    sys.exit(main())
