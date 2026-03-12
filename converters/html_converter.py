"""HTML/网页 转 Markdown 转换器"""
from pathlib import Path


def convert_html(input_path, output_dir, **kwargs):
    """将 HTML 文件转换为 Markdown。

    支持 .html, .htm, .mhtml 格式。

    Args:
        input_path: HTML文件路径
        output_dir: 输出目录

    Returns:
        转换后的Markdown文本
    """
    import markdownify
    from bs4 import BeautifulSoup
    import re

    input_path = Path(input_path)

    # 读取文件，尝试多种编码
    content = _read_html_file(input_path)

    # 处理 MHTML 格式
    if input_path.suffix.lower() == '.mhtml':
        content = _extract_mhtml_body(content)

    # 解析 HTML
    soup = BeautifulSoup(content, 'html.parser')

    # 提取标题
    title = ""
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        title = title_tag.string.strip()

    # 移除不需要的元素
    for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()

    # 尝试提取主要内容区域
    main_content = (
        soup.find('main')
        or soup.find('article')
        or soup.find(attrs={'role': 'main'})
        or soup.find('div', class_=re.compile(r'content|article|post|main', re.I))
        or soup.find('body')
        or soup
    )

    html = str(main_content)

    # 转换为 Markdown
    md_text = markdownify.markdownify(
        html,
        heading_style="atx",
        bullets="-",
        strip=['script', 'style', 'nav', 'footer'],
    )

    # 添加标题（如果有）
    if title:
        md_text = f"# {title}\n\n{md_text}"

    # 清理
    md_text = re.sub(r'\n{4,}', '\n\n\n', md_text)
    md_text = md_text.strip() + '\n'

    return md_text


def _read_html_file(file_path):
    """读取 HTML 文件，自动检测编码。"""
    raw = file_path.read_bytes()

    # 先尝试 UTF-8
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        pass

    # 尝试从 HTML meta 标签检测编码
    import re
    meta_match = re.search(
        rb'<meta[^>]+charset=["\']?([a-zA-Z0-9_-]+)',
        raw[:4096],
    )
    if meta_match:
        encoding = meta_match.group(1).decode('ascii')
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            pass

    # 使用 chardet
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

    # 回退
    for encoding in ['gbk', 'gb2312', 'latin-1']:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    return raw.decode('utf-8', errors='replace')


def _extract_mhtml_body(content):
    """从 MHTML 文件中提取 HTML 正文。"""
    import re

    # MHTML 是多部分 MIME 格式
    # 查找 Content-Type: text/html 部分
    parts = re.split(r'------=_', content)

    for part in parts:
        if 'Content-Type: text/html' in part[:500]:
            # 找到 HTML 部分，跳过 MIME 头
            header_end = part.find('\n\n')
            if header_end >= 0:
                html_body = part[header_end + 2:]

                # 检查是否是 Base64 编码
                if 'Content-Transfer-Encoding: base64' in part[:header_end]:
                    import base64
                    try:
                        html_body = base64.b64decode(html_body).decode('utf-8', errors='replace')
                    except Exception:
                        pass
                # 检查是否是 Quoted-Printable 编码
                elif 'Content-Transfer-Encoding: quoted-printable' in part[:header_end]:
                    import quopri
                    try:
                        html_body = quopri.decodestring(html_body.encode()).decode('utf-8', errors='replace')
                    except Exception:
                        pass

                return html_body

    # 如果没找到特定部分，返回整个内容
    return content
