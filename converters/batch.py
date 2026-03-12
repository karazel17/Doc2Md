"""批量文档转换引擎

递归扫描目录，批量转换文档为 Markdown 格式。
"""
import os
import time
from pathlib import Path
from . import EXTENSION_MAP, TYPE_EXTENSIONS


def scan_files(input_dir, selected_types):
    """递归扫描目录，找到所有待转换的文件。

    Args:
        input_dir: 输入目录路径
        selected_types: 选中的文件类型列表，如 ['PDF', 'Word', 'PPT']

    Returns:
        排序后的文件路径列表
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise ValueError(f"输入目录不存在: {input_dir}")

    # 收集所有选中类型的扩展名
    extensions = set()
    for type_name in selected_types:
        exts = TYPE_EXTENSIONS.get(type_name, [])
        extensions.update(exts)

    files = []
    for root, dirs, filenames in os.walk(input_dir):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in filenames:
            # 跳过隐藏文件和临时文件
            if filename.startswith('.') or filename.startswith('~'):
                continue
            ext = Path(filename).suffix.lower()
            if ext in extensions:
                files.append(Path(root) / filename)

    return sorted(files)


def get_output_path(input_file, input_dir, output_dir):
    """根据输入文件路径计算输出文件路径，保持目录结构。

    Args:
        input_file: 输入文件路径
        input_dir: 输入根目录
        output_dir: 输出根目录

    Returns:
        输出 .md 文件的路径
    """
    rel_path = Path(input_file).relative_to(input_dir)
    output_path = Path(output_dir) / rel_path.with_suffix('.md')
    return output_path


def convert_single_file(input_file, input_dir, output_dir, enable_ocr=True, use_mineru=False):
    """转换单个文件。

    Args:
        input_file: 输入文件路径
        input_dir: 输入根目录
        output_dir: 输出根目录
        enable_ocr: 是否启用OCR
        use_mineru: 是否使用MinerU

    Returns:
        (success, output_path, message) 元组
    """
    input_file = Path(input_file)
    ext = input_file.suffix.lower()

    if ext not in EXTENSION_MAP:
        return False, None, f"不支持的文件格式: {ext}"

    type_name, converter = EXTENSION_MAP[ext]

    # 计算输出路径
    output_path = get_output_path(input_file, input_dir, output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        start_time = time.time()
        md_content = converter(
            input_path=input_file,
            output_dir=output_path.parent,
            enable_ocr=enable_ocr,
            use_mineru=use_mineru,
        )
        elapsed = time.time() - start_time

        # 写入 Markdown 文件
        output_path.write_text(md_content, encoding='utf-8')

        return True, output_path, f"成功 ({elapsed:.1f}秒)"

    except Exception as e:
        return False, None, f"错误: {str(e)}"


def batch_convert(input_dir, output_dir, selected_types, enable_ocr=True,
                  use_mineru=False, progress_callback=None):
    """批量转换目录中的文档。

    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        selected_types: 选中的文件类型
        enable_ocr: 是否启用OCR
        use_mineru: 是否使用MinerU
        progress_callback: 进度回调函数 callback(current, total, message)

    Returns:
        (success_count, fail_count, results) 元组
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 扫描文件
    files = scan_files(input_dir, selected_types)
    total = len(files)

    if total == 0:
        if progress_callback:
            progress_callback(0, 0, "未找到匹配的文件")
        return 0, 0, []

    success_count = 0
    fail_count = 0
    results = []

    for i, file_path in enumerate(files):
        rel_path = file_path.relative_to(input_dir)

        if progress_callback:
            progress_callback(i, total, f"正在转换: {rel_path}")

        success, output_path, message = convert_single_file(
            file_path, input_dir, output_dir,
            enable_ocr=enable_ocr,
            use_mineru=use_mineru,
        )

        if success:
            success_count += 1
            status = "OK"
        else:
            fail_count += 1
            status = "FAIL"

        results.append({
            'input': str(rel_path),
            'output': str(output_path) if output_path else None,
            'status': status,
            'message': message,
        })

        if progress_callback:
            progress_callback(
                i + 1, total,
                f"[{status}] {rel_path} - {message}"
            )

    return success_count, fail_count, results
