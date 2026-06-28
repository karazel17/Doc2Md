"""Doc2Md 常量定义。"""

APP_NAME = "Doc2Md"
APP_VERSION = "2.0.0"

# 支持的文件类型（与 converters/__init__.py 的 TYPE_EXTENSIONS 保持一致）
SUPPORTED_FILE_TYPES = ["PDF", "Word", "PPT", "EPUB", "TXT", "HTML"]

# 类型到扩展名的映射（用于 UI 勾选与扫描过滤）
FILE_TYPE_EXTENSIONS = {
    "PDF": [".pdf"],
    "Word": [".docx", ".doc"],
    "PPT": [".pptx", ".ppt"],
    "EPUB": [".epub"],
    "TXT": [".txt"],
    "HTML": [".html", ".htm", ".mhtml"],
}

# 默认输出目录名（当用户未指定输出目录时，在输入目录旁创建）
DEFAULT_OUTPUT_DIR_NAME = "markdown_output"

# MinerU 模式选项
MINERU_MODES = ["auto", "txt", "ocr"]

# 主题选项
THEME_OPTIONS = ["system", "light", "dark"]
