"""PDF 转 Markdown 转换器

支持:
- 文本PDF: 使用 pymupdf4llm 直接提取
- 扫描件PDF: 使用 RapidOCR 进行 OCR 识别
- MinerU: 可选的高质量 PDF 转换后端
"""
import os
import re
import sys
from pathlib import Path


def convert_pdf(input_path, output_dir, enable_ocr=True, use_mineru=False, **kwargs):
    """将PDF转换为Markdown。"""
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if use_mineru:
        try:
            return _convert_with_mineru(input_path, output_dir)
        except Exception as e:
            raise RuntimeError(f"MinerU 转换失败: {e}")

    return _convert_default(input_path, output_dir, enable_ocr)


def _convert_default(input_path, output_dir, enable_ocr):
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


def _extract_with_pymupdf4llm(input_path, output_dir):
    """使用 pymupdf4llm 提取文本PDF。"""
    import pymupdf4llm

    images_dir = output_dir / f"{input_path.stem}_images"
    images_dir.mkdir(parents=True, exist_ok=True)

    md_text = pymupdf4llm.to_markdown(
        str(input_path),
        write_images=True,
        image_path=str(images_dir),
    )

    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()

    md_text = re.sub(r'\n{4,}', '\n\n\n', md_text)
    return md_text


def _ocr_pdf(input_path, output_dir):
    """对扫描件PDF执行OCR识别。"""
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


def _convert_with_mineru(input_path, output_dir):
    """使用 MinerU (magic-pdf) 进行高质量PDF转换，直接用 Python API。"""
    import shutil
    import tempfile

    # 确保环境变量设置正确（国内网络）
    os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
    os.environ['TRANSFORMERS_OFFLINE'] = '1'

    # 读取 PDF 文件
    pdf_bytes = input_path.read_bytes()

    # 创建临时输出目录
    temp_dir = tempfile.mkdtemp(prefix="mineru_")
    temp_path = Path(temp_dir)

    try:
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
        from magic_pdf.data.dataset import PymuDocDataset
        from magic_pdf.libs.config_reader import get_local_models_dir

        # 创建输出 writer
        local_image_dir = str(temp_path / "images")
        os.makedirs(local_image_dir, exist_ok=True)

        image_writer = FileBasedDataWriter(local_image_dir)
        md_writer = FileBasedDataWriter(str(temp_path))

        # 创建数据集并解析
        ds = PymuDocDataset(pdf_bytes)

        # 根据分类结果选择解析方式
        if ds.classify() == "ocr":
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)

        # 生成 markdown
        md_content = pipe_result.dump_md(md_writer, f"{input_path.stem}.md", "images")

        # 读取输出的 markdown
        md_file = temp_path / f"{input_path.stem}.md"
        if md_file.exists():
            md_content = md_file.read_text(encoding='utf-8')
        else:
            # 尝试查找任意 md 文件
            md_files = list(temp_path.rglob("*.md"))
            if md_files:
                md_content = md_files[0].read_text(encoding='utf-8')
            else:
                raise RuntimeError("MinerU 未生成 Markdown 文件")

        # 复制图片到输出目录
        images_src = temp_path / "images"
        if images_src.exists() and any(images_src.iterdir()):
            images_dst = output_dir / f"{input_path.stem}_images"
            images_dst.mkdir(parents=True, exist_ok=True)
            for img_file in images_src.iterdir():
                if img_file.is_file():
                    shutil.copy2(str(img_file), str(images_dst / img_file.name))
            # 更新 markdown 中的图片路径
            md_content = md_content.replace("images/", f"{input_path.stem}_images/")

        return md_content

    except ImportError:
        # 如果 Python API 不可用，回退到 CLI 方式
        return _convert_with_mineru_cli(input_path, output_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _convert_with_mineru_cli(input_path, output_dir):
    """MinerU CLI 回退方式。"""
    import subprocess
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="mineru_cli_")
    temp_path = Path(temp_dir)

    try:
        # 找到 venv 中的 magic-pdf
        venv_bin = Path(sys.executable).parent
        magic_pdf_cmd = str(venv_bin / 'magic-pdf')

        env = os.environ.copy()
        env['HF_ENDPOINT'] = 'https://hf-mirror.com'
        env['TRANSFORMERS_OFFLINE'] = '1'

        cmd = [magic_pdf_cmd, '-p', str(input_path), '-o', temp_dir, '-m', 'auto']

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, env=env,
        )

        if result.returncode != 0:
            error_msg = result.stderr[-1000:] if result.stderr else "无错误输出"
            raise RuntimeError(f"MinerU CLI 失败:\n{error_msg}")

        # 查找输出的 Markdown
        md_files = list(temp_path.rglob("*.md"))
        if not md_files:
            raise RuntimeError("MinerU 未生成 Markdown 文件")

        md_content = md_files[0].read_text(encoding='utf-8')

        # 复制图片
        images_dst = output_dir / f"{input_path.stem}_images"
        for img_dir in temp_path.rglob("images"):
            if img_dir.is_dir():
                images_dst.mkdir(parents=True, exist_ok=True)
                for img_file in img_dir.iterdir():
                    if img_file.is_file():
                        shutil.copy2(str(img_file), str(images_dst / img_file.name))

        if images_dst.exists() and any(images_dst.iterdir()):
            md_content = re.sub(
                r'!\[(.*?)\]\(.*?/images/(.*?)\)',
                rf'![\1]({input_path.stem}_images/\2)',
                md_content,
            )

        return md_content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def doc_analyze(dataset, *args, **kwargs):
    """MinerU 文档分析入口。"""
    from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze as _doc_analyze
    return _doc_analyze(dataset, *args, **kwargs)
