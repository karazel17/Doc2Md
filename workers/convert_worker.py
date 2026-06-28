"""转换工作线程：QThread 子类，后台执行批量转换。

通过 Signal 安全地跨线程回传进度、单文件结果、日志与最终统计。
支持 cancel() 取消（协作式：循环顶部检查 _cancel 标志）。

注意：本线程直接处理传入的文件列表，不重新扫描目录。
这样确保转换范围与用户在 file_list 中看到的一致。
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.converter_facade import ConverterFacade

logger = logging.getLogger("doc2md")


class ConvertWorker(QThread):
    """批量转换工作线程。

    Signals:
        progress(int, int, str): current, total, current_file_message
        file_done(object): ConvertResult
        finished_all(int, int): success_count, fail_count
        log(str): 日志行
    """

    progress = Signal(int, int, str)
    file_done = Signal(object)
    finished_all = Signal(int, int)
    log = Signal(str)

    def __init__(
        self,
        facade: ConverterFacade,
        files: list[Path],
        input_dir: Path,
        output_dir: Path,
        parent=None,
    ):
        super().__init__(parent)
        self.facade = facade
        self.files = files
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self._cancel = False

    def cancel(self) -> None:
        """请求取消（协作式，在下一次循环迭代顶部生效）。"""
        self._cancel = True
        self.log.emit("收到取消请求，正在停止...")

    def run(self) -> None:
        """工作线程入口。"""
        total = len(self.files)
        if total == 0:
            self.log.emit("没有待转换的文件")
            self.finished_all.emit(0, 0)
            return

        self.log.emit(f"开始转换，共 {total} 个文件")
        self.log.emit(f"输入根目录: {self.input_dir}")
        self.log.emit(f"输出目录: {self.output_dir}")
        cfg = self.facade.config
        self.log.emit(
            f"OCR: {'启用' if cfg.enable_ocr else '关闭'} | "
            f"MinerU: {'启用' if cfg.mineru.enabled else '关闭'}"
            + (f" (模式: {cfg.mineru.mode})" if cfg.mineru.enabled else "")
        )
        self.log.emit("-" * 60)

        success_count = 0
        fail_count = 0

        for i, file_path in enumerate(self.files):
            if self._cancel:
                self.log.emit(f"已取消，已完成 {i}/{total}")
                break

            try:
                rel_path = file_path.relative_to(self.input_dir)
            except ValueError:
                rel_path = file_path

            self.progress.emit(i, total, f"转换中: {rel_path}")

            try:
                result = self.facade.convert_one(
                    file_path, self.input_dir, self.output_dir
                )
                self.file_done.emit(result)

                if result.success:
                    success_count += 1
                    self.log.emit(
                        f"[OK] [{i + 1}/{total}] {rel_path} - {result.message}"
                    )
                else:
                    fail_count += 1
                    self.log.emit(
                        f"[FAIL] [{i + 1}/{total}] {rel_path} - {result.message}"
                    )
            except Exception as e:
                fail_count += 1
                logger.error(f"转换异常: {file_path}", exc_info=True)
                self.log.emit(f"[ERR] [{i + 1}/{total}] {rel_path} - {e}")

            self.progress.emit(i + 1, total, "")

        self.log.emit("-" * 60)
        self.log.emit(
            f"转换结束 | 成功: {success_count} | 失败: {fail_count} | 总计: {total}"
        )
        self.finished_all.emit(success_count, fail_count)
