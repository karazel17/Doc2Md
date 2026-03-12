"""TXT 文本转 Markdown 转换器"""
from pathlib import Path


def convert_txt(input_path, output_dir, **kwargs):
    """将纯文本文件转换为 Markdown。

    自动检测文件编码，支持 UTF-8、GBK、GB2312 等常见中文编码。

    Args:
        input_path: TXT文件路径
        output_dir: 输出目录

    Returns:
        转换后的Markdown文本
    """
    input_path = Path(input_path)

    # 读取文件内容，自动检测编码
    content = _read_with_encoding_detection(input_path)

    # 简单的文本到 Markdown 处理
    lines = content.split('\n')
    md_lines = []

    for line in lines:
        stripped = line.rstrip()
        md_lines.append(stripped)

    result = '\n'.join(md_lines)
    result = result.strip() + '\n'

    return result


def _read_with_encoding_detection(file_path):
    """读取文件，自动检测编码。"""
    raw = file_path.read_bytes()

    # 先尝试 UTF-8
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        pass

    # 尝试带 BOM 的 UTF-8
    if raw.startswith(b'\xef\xbb\xbf'):
        try:
            return raw[3:].decode('utf-8')
        except UnicodeDecodeError:
            pass

    # 使用 chardet 检测编码
    try:
        import chardet
        detected = chardet.detect(raw)
        if detected['encoding']:
            try:
                return raw.decode(detected['encoding'])
            except (UnicodeDecodeError, LookupError):
                pass
    except ImportError:
        pass

    # 尝试常见中文编码
    for encoding in ['gbk', 'gb2312', 'gb18030', 'big5', 'latin-1']:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    # 最后回退：忽略错误
    return raw.decode('utf-8', errors='replace')
