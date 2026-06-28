# Doc2Md

[![Python Tests](https://github.com/karazel17/Doc2Md/actions/workflows/python-test.yml/badge.svg)](https://github.com/karazel17/Doc2Md/actions/workflows/python-test.yml)
[![Release](https://github.com/karazel17/Doc2Md/actions/workflows/release.yml/badge.svg)](https://github.com/karazel17/Doc2Md/actions/workflows/release.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个基于 PySide6 的桌面文档批量转换工具，支持将 PDF、Word、PPT、EPUB、HTML 等多种格式拖拽转换为 Markdown。针对中文 PDF 优化集成 MinerU，识别效果优于 markitdown 等通用方案。

---

## ✨ 特性

- 🖥️ **原生桌面应用** - 基于 PySide6，原生体验，无需浏览器
- 📁 **拖拽识别** - 直接拖入文件/文件夹，自动递归识别并展开
- 📄 **多格式支持** - PDF / Word / PPT / EPUB / HTML / TXT
- 🔍 **OCR 识别** - 自动识别扫描件 PDF（基于 RapidOCR）
- 🚀 **MinerU 增强** - 可选启用 MinerU，对中文 PDF、复杂排版、表格、公式的识别效果显著优于通用方案
- 🖼️ **图片提取** - 自动提取文档中的图片并保留相对路径
- ⚡ **后台转换** - QThread 多线程，UI 不卡顿，支持取消
- 📊 **进度反馈** - 进度条 + 实时日志 + 错误聚合
- ⚙️ **配置持久化** - 设置自动保存，下次启动恢复
- 🔒 **安全** - API Key 等敏感信息文件权限 0600 保护

## 📸 界面预览

> 💡 截图待补充 - 欢迎提交 PR

## 🚀 快速开始

### 方式一：下载打包版本（推荐）

前往 [Releases 页面](https://github.com/karazel17/Doc2Md/releases) 下载对应平台的压缩包：

- **macOS**：`Doc2Md-mac.app.tar.gz`，解压后拖入 Applications
- **Windows**：`Doc2Md-win.zip`，解压后运行 `Doc2Md.exe`
- **Linux**：`Doc2Md-linux.tar.gz`，解压后运行 `Doc2Md`

> **macOS 首次运行提示**：若提示"无法验证开发者"，运行 `xattr -cr /Applications/Doc2Md.app` 解除 Gatekeeper 限制。

### 方式二：从源码运行

**前置要求**：Python 3.10 - 3.12

```bash
git clone https://github.com/karazel17/Doc2Md.git
cd Doc2Md
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### MinerU 模型配置（可选，但推荐中文 PDF 用户启用）

MinerU 模型文件约 1.5GB，不内嵌在安装包中。首次使用 MinerU 前需配置模型目录：

1. **下载模型**：参考 [MinerU 官方文档](https://github.com/opendatalab/MinerU) 下载模型文件
2. **配置路径**：打开 Doc2Md → 菜单"文件" → "设置" → "MinerU 配置" → "模型目录"选择模型所在文件夹
3. **或环境变量**：设置 `MINERU_MODEL_DIR=/path/to/models`

> 未配置模型时，MinerU 会尝试从默认路径或 HuggingFace 下载（国内建议用 `HF_ENDPOINT=https://hf-mirror.com` 镜像）。

---

## 📖 使用指南

### 基本流程

1. **拖入文件** - 将文件或文件夹直接拖入左侧拖拽区，自动识别支持格式
2. **选择输出目录** - 在"输出目录"输入框指定，或点击"浏览"选择
3. **配置选项**（可选）：
   - 勾选要处理的文件类型
   - 启用/禁用 OCR
   - 启用/禁用 MinerU
4. **开始转换** - 点击"▶ 开始转换"按钮
5. **查看结果** - 右侧文件列表实时显示状态，下方日志区显示详细进度

### 高级设置

通过菜单"文件" → "设置"打开设置对话框：

| 配置项 | 说明 |
|--------|------|
| OCR | 对扫描件 PDF 进行文字识别 |
| MinerU 模式 | `auto`（自动判断）/ `txt`（强制文本模式，快）/ `ocr`（强制 OCR，适合扫描件） |
| MinerU 模型目录 | 指定本地模型路径，避免重复下载 |
| LLM 增强 | 预留接口，V2+ 支持图像智能描述（OpenAI 兼容 API） |
| 主题 | system / light / dark |

### 输出结构

转换会保持原始目录结构：

```
output/
└── [原目录名]/
    ├── [文件名].md          # 转换后的 Markdown
    └── [文件名]_images/     # 提取的图片
```

---

## 📋 支持的文件格式

| 格式 | 扩展名 | 说明 | 依赖 |
|------|--------|------|------|
| PDF | .pdf | 文本型 + 扫描件（OCR）+ MinerU 高质量模式 | PyMuPDF / MinerU / RapidOCR |
| Word | .docx | 直接支持 | mammoth |
| Word | .doc | 需 LibreOffice | LibreOffice |
| PowerPoint | .pptx | 直接支持 | python-pptx |
| EPUB | .epub | 电子书 | EbookLib |
| HTML | .html .htm .mhtml | 网页 | BeautifulSoup4 |
| 文本 | .txt | 自动编码检测 | chardet |

---

## 🛠️ 技术栈

### 核心

| 项目 | 用途 | 许可证 |
|------|------|--------|
| **[PySide6](https://www.qt.io/)** | GUI 框架 | LGPL |
| **[MinerU](https://github.com/opendatalab/MinerU)** | 高质量 PDF 解析（中文优化） | AGPL-3.0 |
| **[PyMuPDF](https://github.com/pymupdf/PyMuPDF)** | PDF 渲染与处理 | AGPL-3.0 |
| **[PyMuPDF4LLM](https://github.com/pymupdf/PyMuPDF4LLM)** | PDF 转 Markdown | AGPL-3.0 |

### 文档处理

| 项目 | 用途 |
|------|------|
| mammoth | Word → Markdown |
| python-pptx | PowerPoint 处理 |
| EbookLib | EPUB 处理 |
| BeautifulSoup4 + markdownify | HTML → Markdown |
| RapidOCR | 扫描件 OCR |
| chardet | 文本编码检测 |

### 打包与分发

| 工具 | 用途 |
|------|------|
| [PyInstaller](https://pyinstaller.org/) | 跨平台打包 |
| [GitHub Actions](https://github.com/features/actions) | 三平台 CI/CD |

---

## 📦 开发者指南

### 项目结构

```
Doc2Md/
├── app.py                 # 入口
├── core/                  # 核心层：config / constants / converter_facade
├── converters/            # 格式转换器（保留 V1 设计）
├── workers/               # QThread 工作线程
├── ui/                    # PySide6 界面组件
├── tests/                 # 单元测试
├── build/                 # PyInstaller spec
└── .github/workflows/     # CI/CD
```

### 运行测试

```bash
pip install pytest
pytest tests/ -v
```

### 本地打包

```bash
pip install pyinstaller
pyinstaller build/doc2md.spec --noconfirm
# 产物在 dist/
```

### 架构说明

- **core/**：业务核心，不依赖 UI，可独立测试
- **converters/**：各格式转换器，保留 V1 设计，仅 pdf_converter.py 修复了 MinerU 集成
- **workers/**：QThread 子类，后台执行批量转换，通过 Signal 安全回传 UI
- **ui/**：PySide6 组件，通过信号槽解耦

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

> **注意**：本项目依赖的 MinerU、PyMuPDF、EbookLib 等采用 AGPL-3.0 许可证，分发时请遵守相应要求。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系

如有问题或建议，欢迎通过 [GitHub Issues](https://github.com/karazel17/Doc2Md/issues) 联系。
