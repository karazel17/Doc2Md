"""进度面板组件：进度条 + 日志 + 错误聚合。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ProgressPanel(QWidget):
    """进度与日志面板。

    包含：进度条、当前文件标签、日志文本框、错误计数标签。
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 进度区
        progress_layout = QHBoxLayout()
        self._progress_label = QLabel("就绪")
        self._progress_label.setStyleSheet("font-weight: bold;")
        progress_layout.addWidget(self._progress_label)
        progress_layout.addStretch()
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #666;")
        progress_layout.addWidget(self._count_label)
        layout.addLayout(progress_layout)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%v / %m (%p%)")
        layout.addWidget(self._progress_bar)

        # 日志区
        log_label = QLabel("转换日志")
        log_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(log_label)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            "QTextEdit { font-family: 'Menlo', 'Consolas', monospace; font-size: 12px; }"
        )
        layout.addWidget(self._log, stretch=1)

        # 错误聚合与清空按钮
        footer_layout = QHBoxLayout()
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #e74c3c;")
        footer_layout.addWidget(self._error_label)
        footer_layout.addStretch()

        self._clear_log_btn = QPushButton("清空日志")
        self._clear_log_btn.setFixedWidth(90)
        self._clear_log_btn.clicked.connect(self._log.clear)
        footer_layout.addWidget(self._clear_log_btn)

        layout.addLayout(footer_layout)

        self._error_count = 0
        self._success_count = 0

    def reset(self, total: int = 0) -> None:
        """重置面板状态。"""
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(0)
        self._progress_label.setText("就绪")
        self._count_label.setText(f"共 {total} 个文件" if total > 0 else "")
        self._error_label.setText("")
        self._error_count = 0
        self._success_count = 0

    def update_progress(self, current: int, total: int, message: str) -> None:
        """更新进度条与当前文件标签。"""
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(current)
        if message:
            self._progress_label.setText(message)
        if total > 0:
            self._count_label.setText(f"{current} / {total}")

    def append_log(self, line: str) -> None:
        """追加一行日志。"""
        self._log.append(line)

        # 统计成功/失败
        if line.startswith("[OK]"):
            self._success_count += 1
        elif line.startswith("[FAIL]") or line.startswith("[ERR]"):
            self._error_count += 1

        self._update_error_label()

    def on_finished(self, success: int, fail: int) -> None:
        """转换完成时调用。"""
        self._progress_label.setText(f"完成：成功 {success}，失败 {fail}")
        self._success_count = success
        self._error_count = fail
        self._update_error_label()

    def _update_error_label(self) -> None:
        if self._error_count > 0:
            self._error_label.setText(
                f"⚠️ {self._error_count} 个文件失败，{self._success_count} 个成功"
            )
        elif self._success_count > 0:
            self._error_label.setText(f"✓ 全部成功（{self._success_count} 个）")
        else:
            self._error_label.setText("")
