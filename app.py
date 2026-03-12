"""
Doc2Md - 文档批量转换为 Markdown 工具

支持格式: PDF(含扫描件OCR)、Word、PPT、EPUB、TXT、HTML
支持整目录递归转换，保持原始目录结构
"""
import os
import sys
from pathlib import Path

import gradio as gr

from converters.batch import scan_files, batch_convert


# ───────────────────── 辅助函数 ─────────────────────

def check_mineru_available():
    """检查 MinerU 是否可用（轻量级检查）。"""
    try:
        import importlib.util
        return importlib.util.find_spec("magic_pdf") is not None
    except Exception:
        return False


def preview_files(input_dir, file_types):
    """预览待转换的文件列表。"""
    if not input_dir:
        return "请输入目录路径（可从 Finder 直接拖入文件夹）"

    input_dir = input_dir.strip()
    if not os.path.isdir(input_dir):
        return f"目录不存在: {input_dir}\n请检查路径是否正确"

    if not file_types:
        return "请至少选择一种文件类型"

    try:
        files = scan_files(input_dir, file_types)
    except Exception as e:
        return f"扫描目录出错: {e}"

    if not files:
        return "未找到匹配的文件"

    input_path = Path(input_dir)
    lines = [f"共找到 {len(files)} 个文件:\n"]

    current_dir = None
    for f in files:
        rel = f.relative_to(input_path)
        parent = str(rel.parent)
        if parent != current_dir:
            current_dir = parent
            if parent == '.':
                lines.append(f"\n[根目录]")
            else:
                lines.append(f"\n[{parent}]")
        ext = f.suffix.lower()
        type_icon = {
            '.pdf': 'PDF', '.docx': 'DOC', '.doc': 'DOC',
            '.pptx': 'PPT', '.ppt': 'PPT', '.epub': 'EPUB',
            '.txt': 'TXT', '.html': 'HTML', '.htm': 'HTML', '.mhtml': 'HTML',
        }.get(ext, '???')
        lines.append(f"  [{type_icon}] {rel.name}")

    return "\n".join(lines)


# ───────────────────── 核心转换逻辑 ─────────────────────

def run_conversion(input_dir, output_dir, file_types, enable_ocr, use_mineru):
    """执行批量转换（生成器，流式输出日志）。"""

    if not input_dir:
        yield "请输入源文档目录路径"
        return
    input_dir = input_dir.strip()

    if not os.path.isdir(input_dir):
        yield f"输入目录不存在: {input_dir}"
        return

    if not output_dir:
        yield "请输入输出目录路径"
        return
    output_dir = output_dir.strip()

    if not file_types:
        yield "请至少选择一种文件类型"
        return

    # MinerU 可用性检查
    if use_mineru and not check_mineru_available():
        yield ("MinerU 未安装或不可用，将使用默认转换引擎继续...\n")
        use_mineru = False

    # 扫描文件
    try:
        files = scan_files(input_dir, file_types)
    except Exception as e:
        yield f"扫描目录失败: {e}"
        return

    total = len(files)
    if total == 0:
        yield "未找到匹配的文件，请检查目录路径和文件类型选择"
        return

    log_lines = []
    log_lines.append(f"{'='*50}")
    log_lines.append(f"  Doc2Md 文档批量转换")
    log_lines.append(f"{'='*50}")
    log_lines.append(f"输入目录: {input_dir}")
    log_lines.append(f"输出目录: {output_dir}")
    log_lines.append(f"文件类型: {', '.join(file_types)}")
    log_lines.append(f"OCR识别: {'开启' if enable_ocr else '关闭'}")
    log_lines.append(f"MinerU: {'开启' if use_mineru else '关闭'}")
    log_lines.append(f"待转换文件: {total} 个")
    log_lines.append(f"{'='*50}\n")
    yield "\n".join(log_lines)

    success_count = 0
    fail_count = 0
    input_path = Path(input_dir)

    for i, file_path in enumerate(files):
        rel_path = file_path.relative_to(input_path)
        progress = f"[{i+1}/{total}]"

        log_lines.append(f"{progress} 正在转换: {rel_path} ...")
        yield "\n".join(log_lines)

        from converters.batch import convert_single_file
        success, output_path, message = convert_single_file(
            file_path, input_dir, output_dir,
            enable_ocr=enable_ocr,
            use_mineru=use_mineru,
        )

        if success:
            success_count += 1
            log_lines[-1] = f"{progress} {rel_path} -> {message}"
        else:
            fail_count += 1
            log_lines[-1] = f"{progress} {rel_path} -> {message}"

        yield "\n".join(log_lines)

    log_lines.append(f"\n{'='*50}")
    log_lines.append(f"  转换完成!")
    log_lines.append(f"  成功: {success_count} 个文件")
    if fail_count > 0:
        log_lines.append(f"  失败: {fail_count} 个文件")
    log_lines.append(f"  输出目录: {output_dir}")
    log_lines.append(f"{'='*50}")
    yield "\n".join(log_lines)


# ───────────────────── Gradio 界面 ─────────────────────

MINERU_AVAILABLE = check_mineru_available()

with gr.Blocks(title="Doc2Md - 文档转Markdown") as app:

    gr.Markdown(
        "# Doc2Md - 文档批量转换为 Markdown\n"
        "支持 PDF(含扫描件) / Word / PPT / EPUB / TXT / HTML，整目录递归转换"
    )

    with gr.Row():
        # ── 左侧：目录和选项 ──
        with gr.Column(scale=1):
            gr.Markdown("### 目录设置\n"
                        "提示: 可以从 Finder 直接拖入文件夹到下方输入框")

            input_dir = gr.Textbox(
                label="输入目录（包含文档的文件夹路径）",
                placeholder="例如: /Users/yourname/Documents/我的文档",
            )

            output_dir = gr.Textbox(
                label="输出目录（Markdown 文件保存位置）",
                placeholder="例如: /Users/yourname/Documents/markdown输出",
            )

            gr.Markdown("### 转换选项")

            file_types = gr.CheckboxGroup(
                choices=["PDF", "Word", "PPT", "EPUB", "TXT", "HTML"],
                value=["PDF", "Word", "PPT", "EPUB", "TXT", "HTML"],
                label="要处理的文件类型",
            )

            with gr.Row():
                enable_ocr = gr.Checkbox(
                    label="启用 OCR 识别（扫描件PDF）",
                    value=True,
                )
                use_mineru = gr.Checkbox(
                    label="使用 MinerU 转换 PDF" + ("" if MINERU_AVAILABLE else " (未安装)"),
                    value=MINERU_AVAILABLE,
                    interactive=True,
                )

            with gr.Row():
                preview_btn = gr.Button("预览文件列表", variant="secondary")
                start_btn = gr.Button("开始转换", variant="primary", size="lg")

        # ── 右侧：预览和日志 ──
        with gr.Column(scale=1):
            gr.Markdown("### 文件预览")
            preview_output = gr.Textbox(
                label="待转换文件",
                lines=8,
                interactive=False,
            )

            gr.Markdown("### 转换日志")
            log_output = gr.Textbox(
                label="转换进度",
                lines=15,
                interactive=False,
                autoscroll=True,
            )

    with gr.Accordion("使用说明", open=False):
        gr.Markdown("""
**基本用法:**
1. 在**输入目录**框中粘贴或拖入包含文档的文件夹路径（支持嵌套子文件夹）
2. 在**输出目录**框中填入 Markdown 文件的保存位置
3. 选择需要处理的**文件类型**
4. 点击**预览文件列表**确认待转换的文件
5. 点击**开始转换**

**获取文件夹路径的方法:**
- 在 Finder 中找到文件夹，直接拖入输入框
- 或右键文件夹 -> 显示简介 -> 复制"位置"路径

**格式支持:**
| 格式 | 扩展名 | 说明 |
|------|--------|------|
| PDF | .pdf | 支持文本PDF和扫描件（需启用OCR） |
| Word | .docx, .doc | .doc格式需要安装LibreOffice |
| PPT | .pptx, .ppt | .ppt格式需要安装LibreOffice |
| EPUB | .epub | 电子书格式 |
| TXT | .txt | 自动检测编码（支持中文编码） |
| HTML | .html, .htm, .mhtml | 网页文件 |

**OCR 识别:**
- 启用后可识别扫描件PDF中的文字，支持中英文
- 处理速度较慢，建议仅在有扫描件时开启

**MinerU 模式:**
- 对复杂排版、表格、公式的识别效果更好
        """)

    # ── 事件绑定 ──
    preview_btn.click(
        fn=preview_files,
        inputs=[input_dir, file_types],
        outputs=preview_output,
    )

    start_btn.click(
        fn=run_conversion,
        inputs=[input_dir, output_dir, file_types, enable_ocr, use_mineru],
        outputs=log_output,
    )


# ───────────────────── 启动 ─────────────────────

def find_available_port(start_port=7860, max_attempts=100):
    """查找可用端口，从 start_port 开始递增尝试。"""
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    
    return None


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Doc2Md - 文档批量转换为 Markdown")
    print("="*50)
    
    # 支持环境变量自定义端口
    default_port = int(os.environ.get("DOC2MD_PORT", "7860"))
    
    # 查找可用端口
    port = find_available_port(default_port)
    if port is None:
        print(f"\n错误: 无法找到可用端口 (尝试了 {default_port}-{default_port + 99})")
        print("请检查系统端口占用情况或设置环境变量 DOC2MD_PORT 指定其他端口")
        sys.exit(1)
    
    if port != default_port:
        print(f"\n提示: 默认端口 {default_port} 已被占用，自动切换到端口 {port}")
    
    print(f"\n启动中... 浏览器将自动打开")
    print(f"访问地址: http://127.0.0.1:{port}\n")

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        inbrowser=True,
    )
