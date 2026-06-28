"""主窗口：布局 + 信号槽链 + 转换流程编排。"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.config import AppConfig, ConfigManager
from core.constants import DEFAULT_OUTPUT_DIR_NAME, SUPPORTED_FILE_TYPES
from core.converter_facade import ConverterFacade
from workers.convert_worker import ConvertWorker
from .drop_area import DropArea
from .file_list import FileList
from .progress_panel import ProgressPanel
from .settings_dialog import SettingsDialog

logger = logging.getLogger("doc2md")


class MainWindow(QMainWindow):
    """Doc2Md 主窗口。"""

    def __init__(self, config: AppConfig):
        super().__init__()
        self._config = config
        self._facade = ConverterFacade(config)
        self._worker: ConvertWorker | None = None

        self.setWindowTitle("Doc2Md - 文档批量转换为 Markdown")
        self.resize(config.window_width, config.window_height)

        self._init_ui()
        self._init_menu()
        self._init_signals()
        self._restore_state()

    # ─────────────────── UI 初始化 ───────────────────

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ── 左侧：拖拽区 + 选项 + 按钮 ──
        left = QWidget()
        left_layout = QVBoxLayout(left)

        self._drop_area = DropArea()
        left_layout.addWidget(self._drop_area)

        # 文件类型勾选
        type_group = QGroupBox("文件类型")
        type_layout = QVBoxLayout(type_group)
        self._type_checks: dict[str, QCheckBox] = {}
        for t in SUPPORTED_FILE_TYPES:
            cb = QCheckBox(t)
            cb.setChecked(t in self._config.file_types)
            self._type_checks[t] = cb
            type_layout.addWidget(cb)
        left_layout.addWidget(type_group)

        # 输出目录
        out_group = QGroupBox("输出目录")
        out_layout = QHBoxLayout(out_group)
        self._output_dir_edit = self._make_dir_edit(
            self._config.output_dir, "选择输出目录"
        )
        browse_out = QPushButton("浏览...")
        browse_out.setFixedWidth(80)
        browse_out.clicked.connect(self._browse_output_dir)
        out_layout.addWidget(self._output_dir_edit)
        out_layout.addWidget(browse_out)
        left_layout.addWidget(out_group)

        # MinerU / OCR 快捷开关
        opt_group = QGroupBox("快速选项")
        opt_layout = QVBoxLayout(opt_group)
        self._ocr_check = QCheckBox("启用 OCR（扫描件 PDF）")
        self._ocr_check.setChecked(self._config.enable_ocr)
        opt_layout.addWidget(self._ocr_check)
        self._mineru_check = QCheckBox("使用 MinerU 转换 PDF")
        self._mineru_check.setChecked(self._config.mineru.enabled)
        opt_layout.addWidget(self._mineru_check)
        left_layout.addWidget(opt_group)

        # 开始/取消按钮
        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton("▶ 开始转换")
        self._start_btn.setStyleSheet(
            "QPushButton { background-color: #4a90d9; color: white; font-weight: bold; font-size: 14px; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #357abd; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self._start_btn.setFixedHeight(40)
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setFixedHeight(40)
        self._cancel_btn.setEnabled(False)
        btn_layout.addWidget(self._start_btn)
        btn_layout.addWidget(self._cancel_btn)
        left_layout.addLayout(btn_layout)

        left_layout.addStretch()
        splitter.addWidget(left)

        # ── 右侧：文件列表 + 进度面板 ──
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._file_list = FileList()
        right_layout.addWidget(self._file_list, stretch=1)

        self._progress_panel = ProgressPanel()
        self._progress_panel.setMaximumHeight(280)
        right_layout.addWidget(self._progress_panel)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

    def _init_menu(self) -> None:
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")
        add_files_action = QAction("添加文件...", self)
        add_files_action.triggered.connect(self._add_files_dialog)
        file_menu.addAction(add_files_action)

        add_dir_action = QAction("添加文件夹...", self)
        add_dir_action.triggered.connect(self._add_dir_dialog)
        file_menu.addAction(add_dir_action)

        file_menu.addSeparator()
        settings_action = QAction("设置...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()
        quit_action = QAction("退出", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_signals(self) -> None:
        self._drop_area.files_dropped.connect(self._on_files_dropped)
        self._start_btn.clicked.connect(self._on_start)
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._file_list.remove_all_requested.connect(self._on_clear_list)

        # 同步快捷选项到 config
        self._ocr_check.toggled.connect(self._on_quick_option_changed)
        self._mineru_check.toggled.connect(self._on_quick_option_changed)

    def _restore_state(self) -> None:
        # 恢复输出目录等设置
        if self._config.input_dir:
            # 如果有保存的输入目录，不做自动加载（用户拖拽为主）
            pass

    # ─────────────────── 工具函数 ───────────────────

    def _make_dir_edit(self, value: str, placeholder: str) -> QLineEdit:
        edit = QLineEdit(value or "")
        edit.setPlaceholderText(placeholder)
        return edit

    def _browse_output_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if d:
            self._output_dir_edit.setText(d)

    def _add_files_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "文档文件 (*.pdf *.docx *.doc *.pptx *.ppt *.epub *.txt *.html *.htm *.mhtml);;所有文件 (*)",
        )
        if files:
            self._on_files_dropped([Path(f) for f in files])

    def _add_dir_dialog(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if d:
            self._on_files_dropped([Path(d)])

    # ─────────────────── 信号槽 ───────────────────

    def _on_files_dropped(self, files: list[Path]) -> None:
        if not files:
            return
        # 推断公共父目录作为输入根目录
        base_dir = self._infer_base_dir(files)
        self._file_list.add_files(files, base_dir)

        # 若输出目录为空，自动填充一个建议路径
        if not self._output_dir_edit.text().strip() and base_dir:
            suggested = base_dir.parent / DEFAULT_OUTPUT_DIR_NAME
            self._output_dir_edit.setText(str(suggested))

    def _on_clear_list(self) -> None:
        self._progress_panel.reset()

    def _on_quick_option_changed(self) -> None:
        self._config.enable_ocr = self._ocr_check.isChecked()
        self._config.mineru.enabled = self._mineru_check.isChecked()

    def _on_start(self) -> None:
        all_files = self._file_list.get_files()
        if not all_files:
            QMessageBox.information(self, "提示", "请先拖入文件或文件夹")
            return

        # 根据勾选类型过滤文件
        from converters import TYPE_EXTENSIONS

        selected_types = [
            t for t, cb in self._type_checks.items() if cb.isChecked()
        ]
        if not selected_types:
            QMessageBox.information(self, "提示", "请至少勾选一种文件类型")
            return

        selected_exts: set[str] = set()
        for t in selected_types:
            selected_exts.update(ext.lower() for ext in TYPE_EXTENSIONS.get(t, []))
        files = [f for f in all_files if f.suffix.lower() in selected_exts]

        if not files:
            QMessageBox.information(
                self, "提示", "列表中没有匹配勾选类型的文件"
            )
            return

        output_dir = self._output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.information(self, "提示", "请指定输出目录")
            return
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "错误", f"无法创建输出目录:\n{e}")
            return

        # 推断输入根目录
        input_dir = self._infer_base_dir(files) or Path(files[0]).parent

        # 同步配置
        self._config.output_dir = output_dir
        self._config.input_dir = str(input_dir)
        self._config.file_types = selected_types
        self._config.enable_ocr = self._ocr_check.isChecked()
        self._config.mineru.enabled = self._mineru_check.isChecked()
        ConfigManager.save(self._config)

        # 重建 facade（应用最新配置）
        self._facade = ConverterFacade(self._config)

        # 重置 UI（日志由 worker 负责输出）
        self._file_list.reset_statuses()
        self._progress_panel.reset(total=len(files))

        # 启动工作线程（直接使用 file_list 中的文件，不重新扫描）
        self._worker = ConvertWorker(
            facade=self._facade,
            files=files,
            input_dir=input_dir,
            output_dir=output_dir,
            parent=self,
        )
        self._worker.progress.connect(self._progress_panel.update_progress)
        self._worker.log.connect(self._progress_panel.append_log)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

        # 切换按钮状态
        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._drop_area.setEnabled(False)

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._cancel_btn.setEnabled(False)

    def _on_file_done(self, result) -> None:
        self._file_list.update_item_status(result.input_path, result.success, result.message)

    def _on_finished(self, success: int, fail: int) -> None:
        self._progress_panel.on_finished(success, fail)
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._drop_area.setEnabled(True)
        self._worker = None

        if fail > 0:
            QMessageBox.warning(
                self,
                "转换完成",
                f"转换完成，但 {fail} 个文件失败。\n请查看日志了解详情。",
            )
        else:
            QMessageBox.information(
                self,
                "转换完成",
                f"全部 {success} 个文件转换成功！\n输出目录: {self._output_dir_edit.text()}",
            )

    # ─────────────────── 菜单动作 ───────────────────

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._config, self)
        if dialog.exec() == SettingsDialog.Accepted:
            self._config = dialog.get_config()
            ConfigManager.save(self._config)
            self._facade = ConverterFacade(self._config)
            # 同步 UI 快捷选项
            self._ocr_check.setChecked(self._config.enable_ocr)
            self._mineru_check.setChecked(self._config.mineru.enabled)
            self._output_dir_edit.setText(self._config.output_dir)
            QMessageBox.information(self, "设置已保存", "设置已保存，将在下次转换时生效。")

    def _show_about(self) -> None:
        from core.constants import APP_NAME, APP_VERSION

        QMessageBox.about(
            self,
            "关于",
            f"<h3>{APP_NAME} v{APP_VERSION}</h3>"
            "<p>文档批量转换为 Markdown 工具</p>"
            "<p>支持 PDF（含扫描件 OCR）/ Word / PPT / EPUB / TXT / HTML</p>"
            "<p>基于 MinerU、PyMuPDF、PySide6 等开源项目</p>"
            "<p><a href='https://github.com/karazel17/Doc2Md'>GitHub 仓库</a></p>",
        )

    # ─────────────────── 辅助 ───────────────────

    def _infer_base_dir(self, files: list[Path]) -> Path | None:
        """推断文件的公共父目录作为输入根目录。"""
        if not files:
            return None
        try:
            common = files[0].parent
            for f in files[1:]:
                while common != Path(common.anchor):
                    try:
                        f.relative_to(common)
                        break
                    except ValueError:
                        common = common.parent
                        if common == Path(common.anchor):
                            return None
            return common if common != Path(common.anchor) else None
        except Exception:
            return None

    def closeEvent(self, event) -> None:
        """窗口关闭时保存配置与清理工作线程。"""
        # 保存窗口尺寸
        self._config.window_width = self.width()
        self._config.window_height = self.height()
        self._config.output_dir = self._output_dir_edit.text().strip()
        ConfigManager.save(self._config)

        # 等待工作线程结束
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)

        event.accept()
