"""PDF 转 Markdown 转换器

支持:
- 文本PDF: 使用 pymupdf4llm 直接提取
- 扫描件PDF: 使用 RapidOCR 进行 OCR 识别
- MinerU: 可选的高质量 PDF 转换后端（中文 PDF 识别效果优）
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("doc2md")


def convert_pdf(
    input_path: Path,
    output_dir: Path,
    enable_ocr: bool = True,
    use_mineru: bool = False,
    mineru_cfg: Any = None,
    **kwargs,
) -> str:
    """将 PDF 转换为 Markdown。

    Args:
        input_path: PDF 文件路径
        output_dir: 输出目录（用于存放 .md 与 _images/）
        enable_ocr: 是否对扫描件启用 OCR
        use_mineru: 是否使用 MinerU 后端
        mineru_cfg: MinerUConfig 对象（可选），含 model_dir / mode

    Returns:
        转换后的 Markdown 文本
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if use_mineru:
        try:
            return _convert_with_mineru(input_path, output_dir, mineru_cfg)
        except Exception as e:
            raise RuntimeError(f"MinerU 转换失败: {e}")

    return _convert_default(input_path, output_dir, enable_ocr)


def _convert_default(input_path: Path, output_dir: Path, enable_ocr: bool) -> str:
    """使用 pymupdf + OCR 的默认转换路径。"""
    import pymupdf

    doc = pymupdf.open(str(input_path))

    total_text = ""
    for page in doc:
        total_text += page.get_text()

    has_text = len(total_text.strip()) > 100
    doc.close()

    if has_text:
        return _extract_with_pymupdf4llm(input_path, output_dir)
    elif enable_ocr:
        return _ocr_pdf(input_path, output_dir)
    else:
        return (
            f"<!-- 文件: {input_path.name} -->\n"
            "<!-- 此PDF为扫描件，需要启用OCR功能才能识别内容 -->\n"
        )


def _extract_with_pymupdf4llm(input_path: Path, output_dir: Path) -> str:
    """使用 pymupdf4llm 提取文本 PDF。"""
    import pymupdf4llm

    images_dir = output_dir / f"{input_path.stem}_images"
    images_dir.mkdir(parents=True, exist_ok=True)

    md_text = pymupdf4llm.to_markdown(
        str(input_path),
        write_images=True,
        image_path=str(images_dir),
    )

    # 清理空图片目录
    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()

    md_text = re.sub(r"\n{4,}", "\n\n\n", md_text)
    return md_text


def _ocr_pdf(input_path: Path, output_dir: Path) -> str:
    """对扫描件 PDF 执行 OCR 识别。"""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return (
            f"<!-- 文件: {input_path.name} -->\n"
            "<!-- 此PDF为扫描件，但 rapidocr-onnxruntime 未安装 -->\n"
        )

    import pymupdf

    ocr_engine = RapidOCR()
    doc = pymupdf.open(str(input_path))
    md_parts = []

    images_dir = output_dir / f"{input_path.stem}_images"
    images_dir.mkdir(parents=True, exist_ok=True)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")

        img_path = images_dir / f"page_{page_num + 1}.png"
        pix.save(str(img_path))

        result, _ = ocr_engine(img_bytes)

        page_text_parts = []
        if result:
            result.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
            prev_y = -1
            current_line = []
            for box, text, confidence in result:
                y = box[0][1]
                if prev_y >= 0 and abs(y - prev_y) > 30:
                    if current_line:
                        page_text_parts.append("".join(current_line))
                        current_line = []
                current_line.append(text)
                prev_y = y
            if current_line:
                page_text_parts.append("".join(current_line))

        page_md = "\n\n".join(page_text_parts) if page_text_parts else "(此页未识别到文字)"
        md_parts.append(f"## 第 {page_num + 1} 页\n\n{page_md}")

    doc.close()

    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()

    return "\n\n---\n\n".join(md_parts)


def _convert_with_mineru(
    input_path: Path,
    output_dir: Path,
    mineru_cfg: Any = None,
) -> str:
    """使用 MinerU (magic-pdf) 进行高质量 PDF 转换。

    Args:
        input_path: PDF 文件路径
        output_dir: 输出目录
        mineru_cfg: MinerUConfig 对象（可选）。None 时用默认配置。

    Returns:
        Markdown 文本
    """
    # 模型路径配置化：config > 环境变量 > 默认
    if mineru_cfg is not None and getattr(mineru_cfg, "model_dir", ""):
        os.environ["MINERU_MODEL_DIR"] = mineru_cfg.model_dir
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # 转换模式：auto | txt | ocr
    mode = getattr(mineru_cfg, "mode", "auto") if mineru_cfg else "auto"

    pdf_bytes = input_path.read_bytes()
    temp_path = Path(tempfile.mkdtemp(prefix="mineru_"))

    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze

        # 准备 writer
        local_image_dir = temp_path / "images"
        local_image_dir.mkdir(parents=True, exist_ok=True)
        image_writer = FileBasedDataWriter(str(local_image_dir))
        md_writer = FileBasedDataWriter(str(temp_path))

        # 创建数据集
        ds = PymuDocDataset(pdf_bytes)

        # 根据模式选择解析方式
        # - auto: 用 classify() 自动判断（ocr / txt）
        # - ocr: 强制 OCR 模式（适合扫描件、图片型 PDF）
        # - txt: 强制文本模式（适合纯文本 PDF，速度快）
        if mode == "ocr" or (mode == "auto" and _classify_pdf(ds) == "ocr"):
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)

        # 调用 dump_md 将 Markdown 写入临时目录
        # 注意：dump_md() 返回 None（内容写入文件，不通过返回值返回）
        # 必须从临时文件读取，不能用返回值
        pipe_result.dump_md(md_writer, f"{input_path.stem}.md", "images")

        # 从临时文件读取 Markdown 内容
        md_file = temp_path / f"{input_path.stem}.md"
        if md_file.exists():
            md_content = md_file.read_text(encoding="utf-8")
        else:
            # 兼容：MinerU 可能输出到子目录，查找任意 .md 文件
            md_files = list(temp_path.rglob("*.md"))
            if md_files:
                md_content = md_files[0].read_text(encoding="utf-8")
            else:
                raise RuntimeError("MinerU 未生成 Markdown 文件")

        # 复制图片到输出目录，并安全替换 markdown 中的图片路径
        # 仅匹配 markdown 图片语法 ![alt](images/xxx)，不误伤正文中的 "images/" 文本
        if local_image_dir.exists() and any(local_image_dir.iterdir()):
            images_dst = output_dir / f"{input_path.stem}_images"
            images_dst.mkdir(parents=True, exist_ok=True)
            for img_file in local_image_dir.iterdir():
                if img_file.is_file():
                    shutil.copy2(str(img_file), str(images_dst / img_file.name))
            # 正则替换：![alt](images/xxx) → ![alt]({stem}_images/xxx)
            md_content = re.sub(
                r"(!\[[^\]]*\]\()images/([^)]+)\)",
                rf"\1{input_path.stem}_images/\2)",
                md_content,
            )

        return md_content

    except ImportError as e:
        # Python API 不可用时回退到 CLI
        logger.warning(f"MinerU Python API 不可用，回退到 CLI: {e}")
        return _convert_with_mineru_cli(input_path, output_dir)
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


def _classify_pdf(ds) -> str:
    """安全调用 MinerU 的 classify()，返回 "ocr" 或 "txt"。

    MinerU 2.x 的 PymuDocDataset.classify() 返回值可能是：
    - 字符串 "ocr" / "txt"
    - 枚举 SupportedPdfParseMethod.OCR / .TXT
    本函数统一归一化为小写字符串。

    若 API 变化导致异常，默认返回 "ocr"（更安全，能处理扫描件）。
    """
    try:
        result = ds.classify()
        # 处理字符串
        if isinstance(result, str):
            if result in ("ocr", "txt"):
                return result
            logger.warning(f"MinerU classify() 返回未知字符串: {result}，默认走 OCR 模式")
            return "ocr"
        # 处理枚举（SupportedPdfParseMethod.OCR / .TXT）
        result_str = str(result).lower()
        if "txt" in result_str:
            return "txt"
        if "ocr" in result_str:
            return "ocr"
        logger.warning(f"MinerU classify() 返回未知值: {result}，默认走 OCR 模式")
        return "ocr"
    except Exception as e:
        logger.warning(f"MinerU classify() 调用失败: {e}，默认走 OCR 模式")
        return "ocr"


def _convert_with_mineru_cli(input_path: Path, output_dir: Path) -> str:
    """MinerU CLI 回退方式。"""
    import subprocess
    import sys

    temp_dir = tempfile.mkdtemp(prefix="mineru_cli_")
    temp_path = Path(temp_dir)

    try:
        # 找到 venv 中的 magic-pdf
        venv_bin = Path(sys.executable).parent
        magic_pdf_cmd = str(venv_bin / "magic-pdf")

        env = os.environ.copy()
        env["HF_ENDPOINT"] = "https://hf-mirror.com"
        env["TRANSFORMERS_OFFLINE"] = "1"

        cmd = [magic_pdf_cmd, "-p", str(input_path), "-o", temp_dir, "-m", "auto"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )

        if result.returncode != 0:
            error_msg = result.stderr[-1000:] if result.stderr else "无错误输出"
            raise RuntimeError(f"MinerU CLI 失败:\n{error_msg}")

        # 查找输出的 Markdown
        md_files = list(temp_path.rglob("*.md"))
        if not md_files:
            raise RuntimeError("MinerU 未生成 Markdown 文件")

        md_content = md_files[0].read_text(encoding="utf-8")

        # 复制图片
        images_dst = output_dir / f"{input_path.stem}_images"
        for img_dir in temp_path.rglob("images"):
            if img_dir.is_dir():
                images_dst.mkdir(parents=True, exist_ok=True)
                for img_file in img_dir.iterdir():
                    if img_file.is_file():
                        shutil.copy2(str(img_file), str(images_dst / img_file.name))

        # 安全的图片路径替换（仅匹配 markdown 图片语法）
        if images_dst.exists() and any(images_dst.iterdir()):
            md_content = re.sub(
                r"(!\[[^\]]*\]\().*?/images/(.*?)\)",
                rf"\1{input_path.stem}_images/\2)",
                md_content,
            )

        return md_content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
