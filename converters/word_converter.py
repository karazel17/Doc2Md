"""Word 文档 (.docx/.doc) 转 Markdown 转换器"""
import os
from pathlib import Path


def convert_word(input_path, output_dir, **kwargs):
    """将 Word 文档转换为 Markdown。

    Args:
        input_path: Word文件路径
        output_dir: 输出目录

    Returns:
        转换后的Markdown文本
    """
    input_path = Path(input_path)
    ext = input_path.suffix.lower()

    if ext == '.docx':
        return _convert_docx(input_path, output_dir)
    elif ext == '.doc':
        return _convert_doc(input_path, output_dir)
    else:
        raise ValueError(f"不支持的 Word 格式: {ext}")


def _convert_docx(input_path, output_dir):
    """使用 mammoth 转换 .docx 文件。"""
    import mammoth
    import markdownify

    images_dir = output_dir / f"{input_path.stem}_images"
    image_counter = [0]

    def handle_image(image):
        """提取并保存文档中的图片。"""
        image_counter[0] += 1
        images_dir.mkdir(parents=True, exist_ok=True)

        extension = image.content_type.split('/')[-1]
        if extension == 'jpeg':
            extension = 'jpg'
        filename = f"image_{image_counter[0]}.{extension}"
        filepath = images_dir / filename

        with image.open() as img_stream:
            img_data = img_stream.read()
            filepath.write_bytes(img_data)

        return {
            "src": f"{input_path.stem}_images/{filename}",
            "alt": f"图片 {image_counter[0]}",
        }

    with open(input_path, "rb") as f:
        result = mammoth.convert_to_html(
            f,
            convert_image=mammoth.images.img_element(handle_image),
        )

    html = result.value

    # 转换 HTML 到 Markdown
    md_text = markdownify.markdownify(
        html,
        heading_style="atx",
        bullets="-",
        strip=['script', 'style'],
    )

    # 清理多余空行
    import re
    md_text = re.sub(r'\n{4,}', '\n\n\n', md_text)
    md_text = md_text.strip() + '\n'

    # 清理空的图片目录
    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()

    # 如果有转换警告，附在末尾
    if result.messages:
        warnings = "\n".join(f"- {msg.message}" for msg in result.messages)
        md_text += f"\n\n<!-- 转换警告:\n{warnings}\n-->\n"

    return md_text


def _convert_doc(input_path, output_dir):
    """转换旧版 .doc 文件。

    尝试使用 LibreOffice 先转为 .docx，再进行转换。
    """
    import subprocess
    import tempfile

    # 尝试使用 LibreOffice 转换
    libreoffice_paths = [
        'libreoffice',
        'soffice',
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    ]

    lo_cmd = None
    for path in libreoffice_paths:
        try:
            subprocess.run(
                [path, '--version'],
                capture_output=True,
                timeout=10,
            )
            lo_cmd = path
            break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if lo_cmd is None:
        # 尝试使用 textract 作为后备方案
        try:
            import textract
            text = textract.process(str(input_path)).decode('utf-8')
            return text
        except ImportError:
            pass

        raise RuntimeError(
            ".doc 格式需要安装 LibreOffice 来转换。\n"
            "macOS 安装方法: brew install --cask libreoffice\n"
            "或者将 .doc 文件手动另存为 .docx 格式"
        )

    # 使用 LibreOffice 转换为 docx
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [lo_cmd, '--headless', '--convert-to', 'docx', '--outdir', temp_dir, str(input_path)],
            capture_output=True,
            timeout=120,
        )

        docx_path = Path(temp_dir) / f"{input_path.stem}.docx"
        if docx_path.exists():
            return _convert_docx(docx_path, output_dir)
        else:
            raise RuntimeError(f"LibreOffice 转换 {input_path.name} 失败")
