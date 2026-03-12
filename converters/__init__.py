"""Doc2Md 文档转换器模块"""

from .pdf_converter import convert_pdf
from .word_converter import convert_word
from .ppt_converter import convert_ppt
from .epub_converter import convert_epub
from .txt_converter import convert_txt
from .html_converter import convert_html

# 文件扩展名到转换器的映射
EXTENSION_MAP = {
    '.pdf': ('PDF', convert_pdf),
    '.docx': ('Word', convert_word),
    '.doc': ('Word', convert_word),
    '.pptx': ('PPT', convert_ppt),
    '.ppt': ('PPT', convert_ppt),
    '.epub': ('EPUB', convert_epub),
    '.txt': ('TXT', convert_txt),
    '.html': ('HTML', convert_html),
    '.htm': ('HTML', convert_html),
    '.mhtml': ('HTML', convert_html),
}

# 类型到扩展名的映射
TYPE_EXTENSIONS = {
    'PDF': ['.pdf'],
    'Word': ['.docx', '.doc'],
    'PPT': ['.pptx', '.ppt'],
    'EPUB': ['.epub'],
    'TXT': ['.txt'],
    'HTML': ['.html', '.htm', '.mhtml'],
}

__all__ = [
    'convert_pdf', 'convert_word', 'convert_ppt',
    'convert_epub', 'convert_txt', 'convert_html',
    'EXTENSION_MAP', 'TYPE_EXTENSIONS',
]
