"""文件列表组件：显示待转换文件，转换时更新状态。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class FileList(QWidget):
    """待转换文件列表。

    列：文件名 | 相对路径 | 大小 | 状态
    Signal:
        files_changed(int): 文件数量变化
        remove_all_requested(): 用户点击"清空"
    """

    files_changed = Signal(int)
    remove_all_requested = Signal()

    COL_NAME = 0
    COL_REL_PATH = 1
    COL_SIZE = 2
    COL_STATUS = 3

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        header_layout = QHBoxLayout()
        self._title = QLabel("待转换文件 (0)")
        self._title.setStyleSheet("font-weight: bold; font-size: 13px;")
        header_layout.addWidget(self._title)
        header_layout.addStretch()

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.clicked.connect(self._on_clear)
        header_layout.addWidget(self._clear_btn)

        layout.addLayout(header_layout)

        # 表格
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["文件名", "相对路径", "大小", "状态"])
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_REL_PATH, QHeaderView.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_NAME, QHeaderView.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_SIZE, QHeaderView.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            self.COL_STATUS, QHeaderView.ResizeToContents
        )
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        # 文件路径到行号的映射（用于状态更新）
        self._path_to_row: dict[str, int] = {}

    def add_files(self, files: list[Path], base_dir: Path | None = None) -> None:
        """添加文件到列表（自动去重）。

        Args:
            files: 文件路径列表
            base_dir: 基准目录（用于计算相对路径显示）
        """
        for f in files:
            key = str(f.resolve())
            if key in self._path_to_row:
                continue

            row = self._table.rowCount()
            self._table.insertRow(row)

            # 文件名
            name_item = QTableWidgetItem(f.name)
            name_item.setToolTip(str(f))
            self._table.setItem(row, self.COL_NAME, name_item)

            # 相对路径
            try:
                rel = str(f.relative_to(base_dir)) if base_dir else str(f.parent)
            except ValueError:
                rel = str(f)
            rel_item = QTableWidgetItem(rel)
            rel_item.setToolTip(str(f))
            self._table.setItem(row, self.COL_REL_PATH, rel_item)

            # 大小
            try:
                size = f.stat().st_size
                size_str = self._format_size(size)
            except OSError:
                size_str = "-"
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setItem(row, self.COL_SIZE, size_item)

            # 状态
            status_item = QTableWidgetItem("待转换")
            status_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, self.COL_STATUS, status_item)

            self._path_to_row[key] = row

        self._update_title()

    def clear(self) -> None:
        """清空文件列表。"""
        self._table.setRowCount(0)
        self._path_to_row.clear()
        self._update_title()

    def update_item_status(self, file_path: Path, success: bool, message: str) -> None:
        """更新某文件的状态显示。

        Args:
            file_path: 文件路径
            success: 是否成功
            message: 状态消息
        """
        key = str(file_path.resolve())
        row = self._path_to_row.get(key)
        if row is None:
            return

        status_text = "✓ 成功" if success else "✗ 失败"
        item = self._table.item(row, self.COL_STATUS)
        if item:
            item.setText(status_text)
            if success:
                item.setForeground(QColor("#27ae60"))
            else:
                item.setForeground(QColor("#e74c3c"))
            item.setToolTip(message)

    def reset_statuses(self) -> None:
        """重置所有文件状态为"待转换"（用于重新转换）。"""
        for row in range(self._table.rowCount()):
            item = self._table.item(row, self.COL_STATUS)
            if item:
                item.setText("待转换")
                item.setForeground(QColor("#7f8c8d"))
                item.setToolTip("")

    def get_files(self) -> list[Path]:
        """返回当前列表中的所有文件路径。"""
        # 反转映射：row -> path
        row_to_path = {v: k for k, v in self._path_to_row.items()}
        return [Path(row_to_path[row]) for row in range(self._table.rowCount())]

    def get_common_base_dir(self) -> Path | None:
        """返回列表中所有文件的公共父目录（用于计算输出结构）。

        如果列表为空或无法确定公共目录，返回 None。
        """
        files = self.get_files()
        if not files:
            return None
        try:
            common = Path(files[0]).parent
            for f in files[1:]:
                while common != Path(common.anchor) and not str(Path(f).resolve()).startswith(
                    str(common.resolve())
                ):
                    common = common.parent
                    if common == Path(common.anchor):
                        break
            return common if common != Path(common.anchor) else None
        except Exception:
            return None

    def _on_clear(self) -> None:
        self.clear()
        self.remove_all_requested.emit()

    def _update_title(self) -> None:
        count = self._table.rowCount()
        self._title.setText(f"待转换文件 ({count})")
        self.files_changed.emit(count)

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小。"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
