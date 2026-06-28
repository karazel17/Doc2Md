"""转换门面：统一转换入口，封装现有 converters/ 模块。

V1 仅做包装；V2+ 在 _llm_postprocess 钩子实现图像描述增强。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from converters import EXTENSION_MAP
from converters.batch import convert_single_file

from .config import AppConfig

logger = logging.getLogger("doc2md")


@dataclass
class ConvertResult:
    """单文件转换结果。"""

    input_path: Path
    output_path: Optional[Path]
    success: bool
    elapsed: float
    message: str
    error: Optional[str] = None


class ConverterFacade:
    """转换门面：对上提供统一接口，对下调度各格式 converter。"""

    def __init__(self, config: AppConfig):
        self.config = config

    def convert_one(
        self,
        input_file: Path,
        input_dir: Path,
        output_dir: Path,
    ) -> ConvertResult:
        """转换单个文件。

        Args:
            input_file: 待转换文件绝对路径
            input_dir: 输入根目录（用于计算相对路径与保留目录结构）
            output_dir: 输出根目录

        Returns:
            ConvertResult
        """
        input_file = Path(input_file)
        ext = input_file.suffix.lower()

        if ext not in EXTENSION_MAP:
            return ConvertResult(
                input_path=input_file,
                output_path=None,
                success=False,
                elapsed=0.0,
                message=f"不支持的格式: {ext}",
                error="unsupported_format",
            )

        start_time = time.time()
        try:
            # 调用现有 converters/batch.py 的 convert_single_file
            # 该函数内部已处理输出路径计算、目录创建、文件写入
            ok, out_path, msg = convert_single_file(
                input_file,
                input_dir,
                output_dir,
                enable_ocr=self.config.enable_ocr,
                use_mineru=self.config.mineru.enabled,
                mineru_cfg=self.config.mineru,
            )
            elapsed = time.time() - start_time

            result = ConvertResult(
                input_path=input_file,
                output_path=Path(out_path) if out_path else None,
                success=ok,
                elapsed=elapsed,
                message=msg,
                error=None if ok else msg,
            )

            # LLM 钩子（V1 空实现，保持接口稳定）
            if ok:
                self._llm_postprocess(result)

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"转换异常: {input_file} | {e}", exc_info=True)
            return ConvertResult(
                input_path=input_file,
                output_path=None,
                success=False,
                elapsed=elapsed,
                message=f"异常: {e}",
                error=str(e),
            )

    def _llm_postprocess(self, result: ConvertResult) -> None:
        """LLM 后处理钩子（V2+ 实现）。

        V1 空实现，保持接口稳定。V2 实现时新增 converters/llm_enhancer.py，
        调用 OpenAI 兼容 API 对图片进行描述，不改动本方法签名。
        """
        if self.config.llm.enabled and self.config.llm.image_describe:
            # TODO V2+: 调用 LLM 对 result.output_path 中的图片引用补充描述
            pass
