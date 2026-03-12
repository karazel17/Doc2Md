"""EPUB 转 Markdown 转换器"""
from pathlib import Path


def convert_epub(input_path, output_dir, **kwargs):
    """将 EPUB 电子书转换为 Markdown。

    Args:
        input_path: EPUB文件路径
        output_dir: 输出目录

    Returns:
        转换后的Markdown文本
    """
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    import markdownify

    input_path = Path(input_path)
    images_dir = output_dir / f"{input_path.stem}_images"
    image_counter = 0

    book = epub.read_epub(str(input_path), options={'ignore_ncx': True})
    md_parts = []

    # 提取书名
    title = book.get_metadata('DC', 'title')
    if title:
        md_parts.append(f"# {title[0][0]}\n")

    # 提取作者
    creator = book.get_metadata('DC', 'creator')
    if creator:
        md_parts.append(f"**作者:** {creator[0][0]}\n")

    # 提取并保存图片
    image_map = {}
    for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
        image_counter += 1
        images_dir.mkdir(parents=True, exist_ok=True)
        ext = item.media_type.split('/')[-1]
        if ext == 'jpeg':
            ext = 'jpg'
        if ext == 'svg+xml':
            ext = 'svg'
        img_filename = f"image_{image_counter}.{ext}"
        img_path = images_dir / img_filename
        img_path.write_bytes(item.get_content())
        # 记录原始路径到新路径的映射
        image_map[item.get_name()] = f"{input_path.stem}_images/{img_filename}"
        # 也记录不含目录前缀的文件名
        basename = Path(item.get_name()).name
        image_map[basename] = f"{input_path.stem}_images/{img_filename}"

    # 提取文档内容
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        try:
            content = item.get_content().decode('utf-8', errors='replace')
        except Exception:
            continue

        soup = BeautifulSoup(content, 'html.parser')

        # 更新图片链接
        for img in soup.find_all('img'):
            src = img.get('src', '')
            # 尝试匹配图片
            src_name = Path(src).name
            if src in image_map:
                img['src'] = image_map[src]
            elif src_name in image_map:
                img['src'] = image_map[src_name]

        # 移除不需要的元素
        for tag in soup.find_all(['script', 'style', 'nav']):
            tag.decompose()

        html = str(soup)
        if not html.strip():
            continue

        md = markdownify.markdownify(
            html,
            heading_style="atx",
            bullets="-",
            strip=['script', 'style'],
        )

        md = md.strip()
        if md and len(md) > 10:
            md_parts.append(md)

    # 清理空的图片目录
    if images_dir.exists() and not any(images_dir.iterdir()):
        images_dir.rmdir()

    import re
    result = "\n\n---\n\n".join(md_parts)
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    return result + '\n'
