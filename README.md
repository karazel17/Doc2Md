# Doc2Md

一个简单易用的文档批量转换工具，支持将 PDF、Word、PPT、EPUB、HTML 等多种格式转换为 Markdown 格式。

## ✨ 特性

- 🖥️ **Web 界面** - 基于 Gradio 的直观操作界面
- 📁 **批量处理** - 支持多文件同时上传转换
- 📄 **多格式支持** - PDF、Word (.docx/.doc)、PPT、EPUB、HTML、TXT
- 🔍 **OCR 识别** - 自动识别扫描件 PDF 内容
- 🖼️ **图片提取** - 自动提取并保存文档中的图片

## 🚀 快速开始

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/Doc2Md.git
cd Doc2Md
chmod +x install.sh && ./install.sh
./start.sh
```

### Windows

```cmd
git clone https://github.com/YOUR_USERNAME/Doc2Md.git
cd Doc2Md
install.bat
start.bat
```

## 📦 依赖说明

### 可选依赖

#### LibreOffice（用于 .doc 文件支持）

旧版 Word 文档（`.doc`）需要 LibreOffice 进行转换。

| 系统 | 安装命令 |
|------|----------|
| macOS | `brew install --cask libreoffice` |
| Ubuntu/Debian | `sudo apt install libreoffice` |
| Windows | [官网下载](https://www.libreoffice.org/download/) |

**注意：** `.docx` 格式不需要 LibreOffice，可直接转换。

#### MinerU（高质量 PDF 转换）

```bash
source venv/bin/activate
pip install "magic-pdf[full]"
```

## 📖 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| PDF | .pdf | 支持文本型和扫描件 PDF |
| Word | .docx | 直接支持 |
| Word | .doc | 需 LibreOffice |
| PowerPoint | .pptx | 直接支持 |
| EPUB | .epub | 电子书格式 |
| HTML | .html, .htm | 网页文件 |
| 文本 | .txt | 纯文本文件 |

## 🙏 致谢

- **[MinerU](https://github.com/opendatalab/MinerU)** - 高质量 PDF 转 Markdown (AGPL-3.0)
- **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)** - PDF 处理库 (AGPL-3.0)
- **[PyMuPDF4LLM](https://github.com/pymupdf/PyMuPDF4LLM)** - PDF 转 Markdown (AGPL-3.0)
- **[RapidOCR](https://github.com/RapidAI/RapidOCR)** - OCR 文字识别 (Apache-2.0)
- **[Gradio](https://github.com/gradio-app/gradio)** - Web 界面框架 (Apache-2.0)

## 📄 许可证

本项目采用 MIT 许可证开源发布。

**注意**：PyMuPDF 和 MinerU 采用 AGPL-3.0 许可证，请参考相关项目了解详情。
