"""拖拽区组件：支持文件/文件夹混合拖入。

拖入文件夹时递归展开，按扩展名白名单过滤。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class DropArea(QFrame):
    """拖拽接收区。

    Signal:
        files_dropped(list): 拖入并展开后的文件路径列表（list[Path]）
    """

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(140)
        self.setObjectName("DropArea")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._label = QLabel("📁 拖入文件或文件夹到这里\n\n支持 PDF / Word / PPT / EPUB / TXT / HTML")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(self._label)

        # 样式：虚线边框 + hover 效果
        self.setStyleSheet(
            """
            QFrame#DropArea {
                border: 2px dashed #bbb;
                border-radius: 8px;
                background-color: #fafafa;
            }
            QFrame#DropArea:hover {
                border-color: #4a90d9;
                background-color: #f0f7ff;
            }
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._label.setText("✅ 松开以添加文件")
            self._label.setStyleSheet("color: #4a90d9; font-size: 14px; font-weight: bold;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._label.setText("📁 拖入文件或文件夹到这里\n\n支持 PDF / Word / PPT / EPUB / TXT / HTML")
        self._label.setStyleSheet("color: #666; font-size: 14px;")

    def dropEvent(self, event: QDropEvent) -> None:
        files: list[Path] = []
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if not p.exists():
                continue
            if p.is_dir():
                files.extend(self._expand_dir(p))
            elif p.is_file():
                files.append(p)

        # 去重并排序
        files = sorted(set(files))

        if files:
            event.acceptProposedAction()
            self.files_dropped.emit(files)
        else:
            event.ignore()

        # 恢复提示文本
        self._label.setText("📁 拖入文件或文件夹到这里\n\n支持 PDF / Word / PPT / EPUB / TXT / HTML")
        self._label.setStyleSheet("color: #666; font-size: 14px;")

    def _expand_dir(self, directory: Path) -> list[Path]:
        """递归展开文件夹，按扩展名白名单过滤。

        跳过隐藏目录（如 .git/）和隐藏/临时文件。

        Args:
            directory: 待展开的文件夹路径

        Returns:
            符合格式要求的文件路径列表
        """
        from converters import EXTENSION_MAP

        result: list[Path] = []
        for f in directory.rglob("*"):
            if not f.is_file():
                continue
            # 跳过隐藏目录中的文件（路径中任何部分以 . 开头）
            try:
                rel_parts = f.relative_to(directory).parts
                if any(
                    part.startswith(".") and part != "."
                    for part in rel_parts[:-1]
                ):
                    continue
            except ValueError:
                pass
            # 跳过隐藏文件和临时文件
            if f.name.startswith((".", "~")):
                continue
            if f.suffix.lower() in EXTENSION_MAP:
                result.append(f)
        return result
